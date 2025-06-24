import asyncio
import websockets
import json
import logging

from consts import (
    USERNAME,
    PASSWORD,
    SUBSCRIPTION_KEY,
    WEBSOCKET_URL,
    STATION_NAME,
    RFID,
)
from login import get_bearer_token
from command_utils import get_command_id, get_ticket


async def send_remote_start():
    logging.info("Starting remote start process...")
    bearer_token = get_bearer_token(USERNAME, PASSWORD)
    command_id = get_command_id(bearer_token, SUBSCRIPTION_KEY)
    ticket_id = get_ticket(bearer_token, SUBSCRIPTION_KEY)

    async with websockets.connect(WEBSOCKET_URL) as websocket:
        ticket_auth_msg = {"type": "TICKET_AUTH", "id": ticket_id}
        await websocket.send(json.dumps(ticket_auth_msg))

        print(f"Sent TICKET_AUTH: {ticket_auth_msg}")
        print(f"Received: {await websocket.recv()}")

        async def send_pings():
            while True:
                await websocket.ping()
                await asyncio.sleep(5)

        asyncio.create_task(send_pings())

        # Simulate RFID scan after delay
        await asyncio.sleep(2)
        custom_command_msg = {
            "type": "CUSTOM_COMMAND",
            "commandId": command_id,
            "stations": [STATION_NAME],
            "parameters": {"connectorId": 1, "idTag": RFID},
        }
        await websocket.send(json.dumps(custom_command_msg))
        print(f"Sent CUSTOM_COMMAND: {custom_command_msg}")

        # Wait for a response from the websocket
        while True:
            msg = await websocket.recv()
            print(f"Received: {msg}")
            msg_json = json.loads(msg)
            if msg_json.get("type") == "RESPONSE":
                payload = json.loads(msg_json.get("payload", "{}"))
                if payload.get("status") == "Accepted":
                    print("Remote start accepted.")
                    break


if __name__ == "__main__":
    asyncio.run(send_remote_start())
