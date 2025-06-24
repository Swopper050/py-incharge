import requests

from consts import TICKET_URL, COMMAND_ID_URL


def get_ticket(bearer_token: str, ocp_subscription_key: str) -> str:
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "nl",
        "Authorization": f"Bearer {bearer_token}",
        "Connection": "keep-alive",
        "Host": "businessspecificapimanglobal.azure-api.net",
        "Ocp-Apim-Subscription-Key": ocp_subscription_key,
        "Origin": "https://myincharge.vattenfall.com",
        "Priority": "u=0",
        "Referer": "https://myincharge.vattenfall.com",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
    }

    response = requests.post(TICKET_URL, headers=headers, json={})
    if response.status_code == 200:
        print("Ticket request failed:", response.status_code, response.text)
        raise ValueError("Failed to get ticket from API")

    ticket = response.text.strip().strip('"')
    print("Got ticket:", ticket)
    return ticket


def get_command_id(bearer_token: str, ocp_subscription_key: str):
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "nl",
        "Authorization": f"Bearer {bearer_token}",
        "Connection": "keep-alive",
        "Host": "businessspecificapimanglobal.azure-api.net",
        "Ocp-Apim-Subscription-Key": ocp_subscription_key,
        "Origin": "https://myincharge.vattenfall.com",
        "Priority": "u=0",
        "Referer": "https://myincharge.vattenfall.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site",
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
    }

    response = requests.get(COMMAND_ID_URL, headers=headers)
    if response.status_code != 200:
        print("Command ID request failed:", response.status_code, response.text)
        raise ValueError("Failed to get command ID from API")

    for command in response.json():
        if command["details"]["name"] == "Remote start transaction":
            return command["commandId"]

    raise ValueError("Remote start transaction command not found")
