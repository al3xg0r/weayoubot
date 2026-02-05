# Your Weather Bot 🌤️

**Your Weather Bot** is a professional, asynchronous Telegram bot designed to deliver accurate weather forecasts on a user-defined schedule. Built with **Python 3.10+** and **Aiogram 3**, it supports private chats, groups, and channels.

## 🚀 Features

* **🌍 Smart Geocoding**: Search for cities in any language with duplicate handling.
* **📊 Dual Forecast Types**: Choose between **Current Weather** (Real-time) or **Daily Forecast** (Max/Min temp, Rain, Sunrise/Sunset).
* **📅 Flexible Scheduling**:
    * Every 2 hours
    * Every 12 hours
    * **Daily at a specific time** (e.g., exactly at 08:00 AM)
* **⚙️ Full Management**:
    * `/settings` menu to change the city, reschedule, or unsubscribe.
    * `/help` command for quick instructions inside Telegram.
* **🌐 Multi-Language Support**: English 🇺🇸, Russian 🇷🇺, Ukrainian 🇺🇦.

## 🛠️ Tech Stack

* **Language**: Python 3.10+
* **Framework**: [Aiogram 3.x](https://github.com/aiogram/aiogram)
* **Database**: SQLite
* **Scheduling**: APScheduler
* **API**: [Open-Meteo](https://open-meteo.com/)

## 👥 Using in Groups & Channels

The bot is perfect for group chats (family, work) or channels.

**Instructions:**
1. **Add the bot** to your Group or Channel.
2. **Promote it to Administrator** (This is required for the bot to send messages).
3. Type `/setup` in the chat.
4. Only group admins can configure the bot.

## 📦 Installation

### 1. Clone
```bash
git clone [https://github.com/YOUR_USERNAME/weayoubot.git](https://github.com/YOUR_USERNAME/weayoubot.git)
cd weayoubot
```

### 2. Install
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure (.env)
Create a `.env` file:
```env
BOT_TOKEN=123456789:YOUR_TOKEN
```

### 4. Run
```bash
python bot.py
```

## 📝 Commands

* `/start` - Initialize.
* `/setup` - Configure weather.
* `/settings` - Manage subscription.
* `/help` - Show instructions.

## 📄 License

[MIT License](LICENSE)