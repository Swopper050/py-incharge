# ⚡PyInCharge - An unofficial Python library for controlling your Vattenfall InCharge charging stations 🔌

_Because manually walking to your EV charger is so 2023_ 🚗💨

Welcome to this unofficial, half-baked but working (on my machine) Python package for controlling your Vattenfall InCharge charging stations.
In essence, this is a Python wrapper around the Vattenfall InCharge web application.

It is born out of the frustration of not being able to control my charging station via Home Assistant, so I set out to develop a Python package with which you at least have _some_ control over your station.

Right now, it can't do a lot, but at least it has these features:

- **Selenium-Powered-Login**: Automates the login process in a not so neat but working way
- **Remote Start**: Start charging your EV without leaving your computer

## 🏗️ Installation

```bash
pip install py-incharge
```

Or if you're feeling adventurous and want to build from source:

```bash
git clone https://github.com/Swopper050/py-incharge.git
cd py-incharge
pip install -e .
```

## 🎮 Quick Start

### Environment Setup

Create a `.env` file or set these environment variables:

```bash
export USERNAME="your@email.com"
export PASSWORD="your_super_secret_password"
export STATION_NAME="EVB-P1234567"
export RFID="12345AB6789C01"
export SUBSCRIPTION_KEY="your_subscription_key_here"
```

### Python API Usage

```python
import asyncio
from vattenfall_charger import send_remote_start

# Charge your car like it's 2024
asyncio.run(send_remote_start())
```

## 🌟 How It Works

1. **Login**: Uses Selenium to authenticate with Vattenfall's portal
2. **Get Tokens**: Retrieves bearer tokens and command IDs
3. **WebSocket Connection**: Establishes a real-time connection
4. **Send Commands**: Sends remote start commands to your charging station
5. **Profit**: Your car starts charging! 🎉

## 🚨 Important Notes

- **Chrome Required**: This package uses Chrome for authentication
- **Credentials**: Keep your credentials safe and never commit them to version control
- **Rate Limits**: Don't spam the API (be nice to the servers)
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
