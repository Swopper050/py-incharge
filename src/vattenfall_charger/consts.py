import os

USERNAME = os.getenv("USERNAME", "your@email.com")
PASSWORD = os.getenv("PASSWORD", "your_vattenfall_password")

STATION_NAME = os.getenv("STATION_NAME", "EVB-P1234567")
RFID = os.getenv("RFID", "12345AB6789C01")
SUBSCRIPTION_KEY = os.getenv("SUBSCRIPTION_KEY", "123456789abcdef1234567890abcdef")

WEBSOCKET_URL = "wss://emobility-cloud.vattenfall.com/remote-commands/command-execution"
TICKET_URL = (
    "https://businessspecificapimanglobal.azure-api.net/remote-commands/editor/tickets"
)
COMMAND_ID_URL = f"https://businessspecificapimanglobal.azure-api.net/remote-commands/publicCommands?stationName={STATION_NAME}"
