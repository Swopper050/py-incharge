import json
import logging
import time
from typing import Optional

import requests
import websocket
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

from py_incharge.utils import find_element_through_shadow


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
        """Login and retrieve bearer token"""
        logging.info("Starting login process...")
        logging.info("Starting the login process to retrieve the bearer token...")

        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--start-maximized")

        logging.info("Waiting for the login page to load...")
        driver = webdriver.Chrome(options=options)
        driver.get("https://myincharge.vattenfall.com/")

        try:
            logging.info("Filling in the login form...")
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

    def get_ticket(self) -> str:
        """Get ticket for websocket authentication"""
        if not self.bearer_token:
            raise ValueError("Must login first before getting ticket")

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
            print("Ticket request failed:", response.status_code, response.text)
            raise ValueError("Failed to get ticket from API")

        return response.text.strip().strip('"')

    def get_remote_start_command_id(self, station_name: str) -> str:
        """Get command ID for remote start transaction"""
        if not self.bearer_token:
            raise ValueError("Must login first before getting command ID")

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

        for command in response.json():
            if command["details"]["name"] == "Remote start transaction":
                return command["commandId"]

        raise ValueError("Remote start transaction command not found")

    def start_remote_transaction(
        self, station_name: str, rfid: str, connector_id: int = 1
    ):
        """Start a remote transaction on the specified station"""
        if not self.bearer_token:
            raise ValueError("Must login first before starting transaction")

        logging.info("Starting remote transaction...")
        command_id = self.get_remote_start_command_id(station_name)
        ticket_id = self.get_ticket()

        ws = websocket.create_connection(InCharge.WEBSOCKET_URL)

        ticket_auth_msg = {"type": "TICKET_AUTH", "id": ticket_id}
        ws.send(json.dumps(ticket_auth_msg))
        logging.info(f"Sent TICKET_AUTH: {ticket_auth_msg}")

        response = ws.recv()
        logging.info(f"Received: {response}")

        time.sleep(1)

        custom_command_msg = {
            "type": "CUSTOM_COMMAND",
            "commandId": command_id,
            "stations": [station_name],
            "parameters": {"connectorId": connector_id, "idTag": rfid},
        }
        ws.send(json.dumps(custom_command_msg))
        logging.info(f"Sent CUSTOM_COMMAND: {custom_command_msg}")

        while True:
            msg = ws.recv()
            logging.info(f"Received: {msg}")
            msg_json = json.loads(msg)
            if msg_json.get("type") == "RESPONSE":
                payload = json.loads(msg_json.get("payload", "{}"))
                if payload.get("status") == "Accepted":
                    logging.info("Remote start accepted.")
                    return True
                elif payload.get("status") == "Rejected":
                    logging.error("Remote start rejected.")
                    return False
