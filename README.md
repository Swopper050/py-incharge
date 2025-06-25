<p align="center">
  <img src="./static/logo.png" alt="PyInCharge Logo" width="300"/>
</p>

<h1 align="center">⚡ PyInCharge</h1>
<p align="center">An unofficial Python library for controlling your Vattenfall InCharge charging stations 🔌</p>

<p align="center"><em>Because manually walking to your EV charger is so 2024 🚗💨</em></p>

Welcome to this unofficial, half-baked but working (on my machine) Python package for controlling your Vattenfall InCharge charging stations.
In essence, this is a Python wrapper around the Vattenfall InCharge web application.

It is born out of the frustration of not being able to control my charging station via Home Assistant, so I set out to develop a Python package with which you at least have _some_ control over your station.

Right now, it has these features:

- **Automatic-Login**: Automates the login process in a not so neat but working way
- **Remote Start**: Start charging your EV without leaving your computer
- **Remote Stop**: Stop charging your EV without leaving your computer either
- **Remote Unlock**: Automatically unlock your EV charging cable
- **Set light intensity**: Useless but hey why not
- **Reset**: Reset your charging station

## 🏗️ Installation

```bash
pip install py-incharge
```

Or from source:

```bash
git clone https://github.com/Swopper050/py-incharge.git
cd py-incharge
pip install -e .
```

## 🎮 Quick Start

### Usage (commands)

```python
import logging
from py_incharge import InChargesend_remote_start

# Optional, to see the logging and what's going on
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

client = InCharge(email="your@email.com", password="your_password")
client.login()  # Required for other calls to work

# Charge your car like it's 2025
client.start_transaction(station_name="EVB-12345678", rfid="123456abcdef")

# Other commands
client.unlock_connector(station_name="EVB-12345678")
client.stop_transaction(station_name="EVB-12345678", transaction_id=1)
client.set_light_intensity(station_name="EVB-12345678", "90")
client.trigger_status_notification(station_name="EVB-12345678")
client.reset(mode="Soft")  # Careful with this one

# Logout to finish the session
client.logout()
```

## 🕵️ Find the information you need in Vattenfall

In order to work with this library you need 4 things:

1. Your email. I really hope you know this one.
2. Your password. Same.

These are your credentials you use to login at the [Vattenvall InCharge portal](https://myincharge.vattenfall.com/):

<p align="center">
  <img src="./static/incharge_login_page.png" alt="Vattenfall InCharge Login Page" width="50%"/>
</p>

3. The name of your charging station, something like `EVB-P1234567`. After logging in to the portal you can find that here:
   ![Find station name](./static/find_station_name.png)

4. The RFID of your charging card. The RFID is something like `12345AB12345C67` (not the same as your card number, which is something like for example `NL-NUO-A01234567-A`). You can your RFID here:
   ![Find RFID](./static/find_rfid.png)

With these 4 variables (email, password, station name and RFID), you can use the package!

## 🌟 How It Works

1. **Login**: Mimics the login flow to obtain a 'bearer token', used to authenticate further requests.
2. **Send Commands**: Now you can send commands like `start_transaction(...)` or `unlock_connector(...)`. For every call roughly the following steps are executed:

   - A new ticket ID is requested.
   - Via a websocket connection this ticket is validated.
   - The command with specific parameters (`station_name`, `connector_id`, `transaction_id`, etc.) is send to the websocket.
   - The reponse status is validated.

3. **Profit**: Your car starts (or stops, or something else) charging! 🎉

## 🚨 Important Notes

- **Chrome Required**: This package uses Chrome for authentication
- **Credentials**: Keep your credentials safe and never commit them to version control
- **Rate Limits**: Don't spam the API (be nice to the servers), especially take time between commands!
- **Testing**: Always test in a safe environment first

## 🤝 Contributing

Found a bug? Want to add a feature? PRs are welcome! Just make sure to:

1. Write clean, documented code
2. Follow the existing code style
3. Add tests (not really, but when you're at it, feel free to test my code too ;) )
4. Update this README if needed

## 📄 License

MIT License - feel free to use this for your own EV charging projects

---

**Disclaimer**: This is an unofficial tool and is not affiliated with Vattenfall. Use at your own risk and always follow local regulations regarding EV charging.
