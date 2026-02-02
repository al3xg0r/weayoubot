
# Your Weather Bot 🌤

Telegram bot for sending weather updates on a schedule.

## 🚀 Functionality
* 🌍 Search for a city by name (Open-Meteo Geocoding).
* 🕒 Interval settings: every 2 hours, 12 hours, or once a day at a specific time.
* 💾 Storing subscribers in SQLite.
* 🔄 Asynchronous delivery without delays.

## 🛠 Stack
* Python 3.10+
* Aiogram 3
* APScheduler
* Aiohttp
* SQLite

## 📦 Installation
1. Clone the repo.
2. Create `.env` with `BOT_TOKEN`.
3. `pip install -r requirements.txt`
4. `python bot.py`

