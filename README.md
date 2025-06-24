# ⚡ Vattenfall Charger Controller 🔌

*Because manually walking to your EV charger is so 2023* 🚗💨

Welcome to the most electrifying Python package you'll ever use! This nifty little tool lets you remotely control your Vattenfall EV charging station from the comfort of your couch, office, or anywhere with an internet connection.

## 🚀 Features That'll Shock You

- **Remote Start**: Start charging your EV without leaving your warm bed
- **WebSocket Magic**: Real-time communication with your charging station
- **Selenium-Powered**: Automates the login process like a digital ninja
- **Environment-Friendly**: Uses environment variables (and saves the planet!)
- **Async/Await**: Because we're not living in the stone age

## 🏗️ Installation

```bash
pip install vattenfall-charger
```

Or if you're feeling adventurous and want to build from source:

```bash
git clone https://github.com/bram/vattenfall-charger.git
cd vattenfall-charger
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

### Command Line Usage

```bash
# Start charging like a boss
vattenfall-charger
```

### Python API Usage

```python
import asyncio
from vattenfall_charger import send_remote_start

# Charge your car like it's 2024
asyncio.run(send_remote_start())
```

## 🔧 Development Setup

Want to contribute? Awesome! Here's how to get started:

```bash
# Clone the repo
git clone https://github.com/bram/vattenfall-charger.git
cd vattenfall-charger

# Install development dependencies
pip install -e ".[dev]"

# Run the linter (because clean code is happy code)
ruff check .

# Format your code (make it pretty)
black .

# Run tests (when we have them)
pytest
```

## 🏗️ Project Structure

```
vattenfall-charger/
├── src/
│   └── vattenfall_charger/
│       ├── __init__.py
│       ├── charger.py      # Main charging logic
│       ├── login.py        # Authentication magic
│       ├── command_utils.py # API utilities
│       └── consts.py       # Configuration constants
├── .github/
│   └── workflows/
│       ├── lint.yml        # Code quality checks
│       └── publish.yml     # Automated publishing
├── setup.py               # Package setup
├── requirements.txt       # Dependencies
├── pyproject.toml        # Modern Python packaging
└── README.md             # This awesome file
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
3. Add tests (when we have a test framework)
4. Update this README if needed

## 📄 License

MIT License - feel free to use this for your own EV charging adventures!

## 🎯 Roadmap

- [ ] Add support for multiple charging stations
- [ ] Implement charging status monitoring
- [ ] Add scheduling capabilities
- [ ] Create a web dashboard
- [ ] Add support for other EV providers (because sharing is caring)

## 💬 Support

Having issues? Found a bug? Want to share your success story?

- 🐛 [Report bugs](https://github.com/bram/vattenfall-charger/issues)
- 💡 [Request features](https://github.com/bram/vattenfall-charger/issues)
- 📚 [Read the docs](https://github.com/bram/vattenfall-charger#readme)

---

*Made with ❤️ and lots of ☕ by developers who are tired of walking to their EV chargers*

**Disclaimer**: This is an unofficial tool and is not affiliated with Vattenfall. Use at your own risk and always follow local regulations regarding EV charging.