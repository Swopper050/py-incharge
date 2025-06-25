import enum
import json
import logging
import time
from typing import Literal, Optional

import requests
import websocket
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from py_incharge.utils import find_element_through_shadow


class Command(enum.Enum):
    unlock_connector = "UnlockConnector"
    start_transaction = "Remote start transaction"
    stop_transaction = "Remote Stop Transaction"
    set_light_intensity = "Set Light intensity"
    change_availability = "Change availability"
    reset = "Reset"
    trigger_status_notification = "TriggerMessage StatusNotificat"


class WebsocketMessageType(enum.Enum):
    ticket_auth = "TICKET_AUTH"
    custom_command = "CUSTOM_COMMAND"
    response = "RESPONSE"
    sent = "SENT"
    ping = "PING"
    error = "ERROR"


class InCharge:
    AZURE_BASE_URL = "https://businessspecificapimanglobal.azure-api.net"

    TICKET_URL = f"{AZURE_BASE_URL}/remote-commands/editor/tickets"
    COMMAND_ID_URL = (
        f"{AZURE_BASE_URL}/remote-commands/publicCommands?stationName={{station_name}}"
    )
    WEBSOCKET_URL = (
        "wss://emobility-cloud.vattenfall.com/remote-commands/command-execution"
    )

    def __init__(self, email: str, password: str, subscription_key: str):
        self.email = email
        self.password = password
        self.subscription_key = subscription_key

        self.bearer_token: Optional[str] = None

    def login(self):
        """
        Login and retrieve bearer token. The bearer token is a token stored by the application in
        the session storage after a successful login. It is used to authenticate API requests
        and websocket connections.

        This method uses Selenium to automate the login process by filling in the email and password fields
        on the login page, submitting the form, and then retrieving the token from the session storage.

        Note: This method requires the Chrome WebDriver to be installed and available in the system PATH.
        """

        logging.info("Starting the login process to retrieve the bearer token...")

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--start-maximized")

        logging.info("Waiting for the login page to load...")
        driver = webdriver.Chrome(options=options)
        driver.get("https://myincharge.vattenfall.com/")

        try:
            logging.info("Filling in email and password...")
            email_input = find_element_through_shadow(
                driver,
                hosts_css_chain=["ic-input[formcontrolname='username']"],
                leaf_css="input",
            )
            email_input.send_keys(self.email)
            time.sleep(0.1)

            password_input = find_element_through_shadow(
                driver,
                hosts_css_chain=["ic-input[formcontrolname='password']"],
                leaf_css="input",
            )
            password_input.send_keys(self.password)
            time.sleep(0.2)

            logging.info("Submitting the login form...")
            password_input.send_keys(Keys.RETURN)
            time.sleep(3)

            logging.info("Waiting for the page to load after login...")
            for _ in range(10):
                token = driver.execute_script(
                    "return window.sessionStorage.getItem('auth_token');"
                )
                if token:
                    logging.info("Bearer token found in session storage.")
                    self.bearer_token = token
                    return

                time.sleep(1)

            driver.quit()

            raise Exception("Token not found in session storage.")
        finally:
            driver.quit()
            logging.info("Login successful, bearer token obtained")

    @staticmethod
    def requires_login(method):
        """Decorator to ensure the user is logged in before executing a method."""

        def wrapper(self, *args, **kwargs):
            if not self.bearer_token:
                raise ValueError("Must login first (call 'client.login()')")
            return method(self, *args, **kwargs)

        return wrapper

    @requires_login
    def unlock_connector(self, station_name, connector_id: int = 1):
        """This will unlock your EV charger."""
        return self._send_command_via_websocket(
            self._get_command_id(station_name, Command.unlock_connector),
            station_name,
            {"example-number-parameter": connector_id},
            expected_status="Unlocked",
        )

    @requires_login
    def start_transaction(self, station_name: str, rfid: str, connector_id: int = 1):
        """This will turn on your EV charger."""
        return self._send_command_via_websocket(
            self._get_command_id(station_name, Command.start_transaction),
            station_name,
            {"connectorId": connector_id, "idTag": rfid},
            expected_status="Accepted",
        )

    @requires_login
    def set_light_intensity(
        self,
        station_name: str,
        intensity: Literal["0", "10", "25", "50", "75", "90", "100"],
    ):
        """This will set the light intensity of the EV charger."""
        return self._send_command_via_websocket(
            self._get_command_id(station_name, Command.set_light_intensity),
            station_name,
            {"example-enum-parameter": intensity},
            expected_status="Accepted",
        )

    @requires_login
    def stop_transaction(self, station_name: str, transaction_id: int = 1):
        """This will turn off your EV charger."""
        return self._send_command_via_websocket(
            self._get_command_id(station_name, Command.stop_transaction),
            station_name,
            {"transactionId": transaction_id},
            expected_status="Accepted",
        )

    @requires_login
    def change_availability(
        self,
        station_name: str,
        availability: Literal["Operative", "Inoperative"],
        connector_id: int = 1,
    ):
        """This will change the availability of the EV charger."""
        return self._send_command_via_websocket(
            self._get_command_id(station_name, Command.change_availability),
            station_name,
            {"connectorId": connector_id, "availability": availability},
            expected_status="Accepted",
        )

    @requires_login
    def reset(self, station_name: str, mode: Literal["Soft", "Hard"] = "Soft"):
        """This will reset the EV charger."""
        return self._send_command_via_websocket(
            self._get_command_id(station_name, Command.reset),
            station_name,
            {"typeOfReset": mode},
            expected_status="Accepted",
        )

    @requires_login
    def trigger_status_notification(self, station_name: str, connector_id: int = 1):
        """This will trigger a status notification for the EV charger."""
        return self._send_command_via_websocket(
            self._get_command_id(station_name, Command.trigger_status_notification),
            station_name,
            {"connectorId": connector_id},
            expected_status="Accepted",
        )

    @requires_login
    def _send_command_via_websocket(
        self, command_id: str, station_name: str, parameters: dict, expected_status: str
    ) -> bool:
        """
        Sends a command via websocket to the InCharge API and waits for a response.
        This method is used for various commands like unlocking a connector, starting a transaction, etc.
        It also checks the response status to determine if the command was accepted or rejected.

        It does the following:
          1. Connects to the InCharge websocket server.
          2. Requests a new ticket id.
          3. Sends a ticket authentication message to the websocket.
          4. Sends a custom command message with the specified command ID, station name, and parameters.
          5. Waits for a response from the websocket and checks the status of the response.
        """

        logging.info("Connecting to websocket")
        ws = websocket.create_connection(self.WEBSOCKET_URL)

        try:
            ticket_auth_msg = {
                "type": WebsocketMessageType.ticket_auth.value,
                "id": self._get_new_ticket_id(),
            }
            ws.send(json.dumps(ticket_auth_msg))

            logging.info(f"Sent ticket authentication to websocket: {ticket_auth_msg}")
            logging.info(f"Received message from websocket: {ws.recv()}")
            time.sleep(1)

            custom_command_msg = {
                "type": WebsocketMessageType.custom_command.value,
                "commandId": command_id,
                "stations": [station_name],
                "parameters": parameters,
            }
            ws.send(json.dumps(custom_command_msg))

            logging.info(f"Sent command to websocket: {custom_command_msg}")

            while True:
                msg = ws.recv()
                logging.info(f"Received message from websocket: {msg}")

                msg_json = json.loads(msg)
                if msg_json.get("type") == WebsocketMessageType.response.value:
                    payload = json.loads(msg_json.get("payload", "{}"))

                    status = payload.get("status")
                    if status == expected_status:
                        logging.info(f"Command accepted: {status}")
                        return True
                    elif status == "Rejected":
                        logging.error(f"Command rejected: {status}")
                        return False
                elif msg_json.get("type") == WebsocketMessageType.error.value:
                    logging.error(
                        f"Error received from websocket: {msg_json.get('payload')}"
                    )
                    return False
        finally:
            ws.close()

    @requires_login
    def _get_new_ticket_id(self) -> str:
        """
        Before starting a remote transaction, a ticket ID must be obtained.
        This ticket is used to authenticate the websocket connection and is required
        to start a remote transaction. This function sends a POST request to the
        InCharge API to obtain a ticket id.
        """
        response = requests.post(
            InCharge.TICKET_URL,
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "Ocp-Apim-Subscription-Key": self.subscription_key,
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
            },
            json={},
        )
        if response.status_code == 200:
            logging.error("Ticket request failed:", response.status_code, response.text)
            raise ValueError("Failed to get ticket from API")

        return response.text.strip().strip('"')

    @requires_login
    def _get_command_id(self, station_name: str, command: Command) -> str:
        """
        Nobody knows why, but the command ID is not static and must be fetched
        from the InCharge API every time before starting a remote transaction.
        This function sends a GET request to the InCharge API to retrieve the command id
        for the remote start transaction command for the specified station.
        """
        response = requests.get(
            InCharge.COMMAND_ID_URL.format(station_name=station_name),
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "Ocp-Apim-Subscription-Key": self.subscription_key,
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
            },
        )
        if response.status_code != 200:
            print("Command ID request failed:", response.status_code, response.text)
            raise ValueError("Failed to get command ID from API")

        for command_info in response.json():
            if command_info["details"]["name"] == command.value:
                return command_info["commandId"]

        raise ValueError(f"Command {command.name} not found")
