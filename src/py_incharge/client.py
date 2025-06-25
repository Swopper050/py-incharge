import base64
import enum
import hashlib
import json
import logging
import os
import re
import time
from typing import Literal, Optional
from urllib.parse import parse_qs, urlparse

import requests
import websocket


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

    AUTHORIZATION_URL = "https://accounts.vattenfall.com/iamng/emob/oauth2/authorize"
    TOKEN_URL = "https://accounts.vattenfall.com/iamng/emob/oauth2/token"
    LOGIN_URL = "https://accounts.vattenfall.com/iamng/emob/commonauth"
    LOGOUT_URL = f"{AZURE_BASE_URL}/jwt-invalidate/invalidate"

    TICKET_URL = f"{AZURE_BASE_URL}/remote-commands/editor/tickets"
    COMMAND_ID_URL = (
        f"{AZURE_BASE_URL}/remote-commands/publicCommands?stationName={{station_name}}"
    )
    WEBSOCKET_URL = (
        "wss://emobility-cloud.vattenfall.com/remote-commands/command-execution"
    )

    REMOTE_COMMANDS_OCP_APIM_SUBSCRIPTION_KEY = "7685786eb9544d97923b0f01ac1b45d8"
    LOGOUT_OCP_APIM_SUBSCRIPTION_KEY = "15dd233179974ff6aa63dc8ae2499a1b"
    """These Ocp-Apim-Subscription-Key values are fixed and global, they are extracted manually
    by analyzing the headers of the network messages in the portal."""

    CLIENT_ID = "Ac5BFlCwsq4AgqvwaqBYv5uVLpJV"
    """Client ID, a static value that is used to identify the application."""

    AUTHORIZATION_REDIRECT_URI = "https://myincharge.vattenfall.com?authType=customer"
    """Redirect URI, a static value that is used to redirect the user after login."""

    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password

        self.bearer_token: Optional[str] = None

    def login(self):
        """
        Login and retrieve bearer token.

        This method performs the following steps:
          1. Initiates a session and retrieves the authorization page.
          2. Extracts the session data key from the authorization page.
          3. Submits the login form with the user's credentials and session data key.
          4. Follows the redirect to the landing page to obtain the authorization code.
          5. Exchanges the authorization code for a bearer token.
          6. Stores the bearer token for future API requests.
        """

        logging.info("Starting the login process to retrieve the bearer token...")

        session = requests.Session()
        code_verifier, code_challenge = InCharge._get_pkce_pair()

        auth_response = session.get(
            InCharge.AUTHORIZATION_URL,
            params={
                "client_id": InCharge.CLIENT_ID,
                "redirect_uri": InCharge.AUTHORIZATION_REDIRECT_URI,
                "response_type": "code",
                "response_mode": "query",
                "scope": "openid profile email offline_access api",
                "state": "incharge_state_string",
                "code_challenge": code_challenge,
                "code_challenge_method": "S256",
                "tenantDomain": "int.incharge",
                "relyingParty": InCharge.CLIENT_ID,
                "sp": "ICSP",
                "isSaaSApp": "false",
                "authenticators": "EmobilityAuthenticator",
                "type": "oidc",
                "forceAuth": "false",
                "passiveAuth": "false",
                "commonAuthCallerPath": "/oauth2/authorize",
            },
        )

        qs = parse_qs(urlparse(auth_response.url).query).get("sessionDataKey")
        if qs is None:
            logging.error("Failed to find sessionDataKey in the authorization URL.")
            raise ValueError("Failed to find sessionDataKey in the authorization URL.")

        session_data_key = qs[0]

        logging.info("Session data key found, proceeding with login...")

        login_response = session.post(
            InCharge.LOGIN_URL,
            data={
                "usernameInput": "int.incharge",
                "username": f"INT.INCHARGE/{self.email}@int.incharge",
                "password": self.password,
                "sessionDataKey": session_data_key,
                "tenantDomain": "int.incharge",
                "captchaToken": "",
            },
            allow_redirects=False,
        )

        if login_response.status_code != 302:
            logging.error(
                f"Login failed with status code {login_response.status_code}: {login_response.text}"
            )
            raise ValueError(
                f"Failed to login to InCharge API: {login_response.status_code} - {login_response.text}"
            )

        logging.info(
            "Login successful, following redirect until we reach the landing page"
        )

        redirect_response = session.get(
            login_response.headers["Location"], allow_redirects=True
        )
        code_match = re.search(r"[?&]code=([^&]+)", redirect_response.url)
        if not code_match:
            logging.error("Auth-code not found after login.")
            raise ValueError("Auth-code not found after login.")

        auth_code = code_match.group(1)

        logging.info("Auth-code found, proceeding to exchange it for a bearer token...")
        token_response = session.post(
            InCharge.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": InCharge.AUTHORIZATION_REDIRECT_URI,
                "client_id": InCharge.CLIENT_ID,
                "code_verifier": code_verifier,
            },
        )

        if token_response.status_code != 200:
            logging.error(
                f"Token exchange failed: {token_response.status_code} - {token_response.text}"
            )
            raise ValueError(
                f"Failed to exchange auth code for bearer token: {token_response.status_code} - {token_response.text}"
            )

        authorization_data = token_response.json()
        bearer_token = authorization_data.get("id_token")

        if bearer_token is None:
            logging.error("Bearer token not found in authorization data.")
            raise ValueError("Bearer token not found in authorization data.")

        self.bearer_token = bearer_token
        logging.info("Bearer token obtained successfully.")

    def logout(self):
        """Logout from the InCharge API by invalidating the session token."""
        response = requests.delete(
            InCharge.LOGOUT_URL,
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "Ocp-Apim-Subscription-Key": InCharge.LOGOUT_OCP_APIM_SUBSCRIPTION_KEY,
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
            },
        )

        if response.status_code == 200:
            logging.info("Logout successful")
            self.bearer_token = None
            return

        logging.error(f"Logout failed: {response.status_code} - {response.text}")
        raise ValueError(
            f"Failed to logout from InCharge API: {response.status_code} - {response.text}"
        )

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
                "Ocp-Apim-Subscription-Key": InCharge.REMOTE_COMMANDS_OCP_APIM_SUBSCRIPTION_KEY,
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
                "Ocp-Apim-Subscription-Key": InCharge.REMOTE_COMMANDS_OCP_APIM_SUBSCRIPTION_KEY,
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

    @staticmethod
    def _get_pkce_pair():
        """Return (code_verifier, code_challenge) for PKCE S256."""
        verifier = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b"=").decode()
        challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )
        return verifier, challenge
