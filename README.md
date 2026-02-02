# Your Weather Bot 🌤️

**Your Weather Bot** is a professional, asynchronous Telegram bot designed to deliver accurate weather forecasts on a user-defined schedule. Built with **Python 3.10+** and **Aiogram 3**, it supports private chats, groups, and channels with role-based access control.

## 🚀 Features

* **🌍 Smart Geocoding**: Search for cities in any language. The bot handles duplicate names (e.g., "Paris, US" vs "Paris, FR") by offering an interactive country selection menu.
* **📅 Flexible Scheduling**:
    * Every 2 hours
    * Every 12 hours
    * **Daily at a specific time** (e.g., exactly at 08:00 AM)
* **⚙️ Full Management**:
    * `/settings` menu to change the city, reschedule, or unsubscribe.
    * Admin-only configuration in groups and channels.
* **🌐 Multi-Language Support**: Automatically detects user language (English 🇺🇸, Russian 🇷🇺, Ukrainian 🇺🇦).
* **⚡ High Performance**: Asynchronous architecture using `aiohttp` and `APScheduler` ensures zero blocking, even with high load.

## 🛠️ Tech Stack

* **Language**: Python 3.10+
* **Framework**: [Aiogram 3.x](https://github.com/aiogram/aiogram)
* **Database**: SQLite (Automatic initialization)
* **Scheduling**: APScheduler (AsyncIOScheduler)
* **API**: [Open-Meteo](https://open-meteo.com/) (No API key required)

## 👥 Using in Groups & Channels

The bot is perfect for group chats (family, work) or channels.

**Instructions:**
1. **Add the bot** to your Group or Channel.
2. **Promote it to Administrator** (This is required for the bot to send messages).
3. Type `/setup` in the chat.
4. Only group admins can configure the bot.

## 📦 Installation & Deployment

### 1. Clone the repository
```bash
git clone https://github.com/al3xg0r/weayoubot.git
cd weayoubot
```

### 2. Set up Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
BOT_TOKEN=123456789:YOUR_TELEGRAM_BOT_TOKEN
```

### 4. Run
```bash
python bot.py
```

## 🖥️ Server Deployment (Systemd)

To run the bot in the background on Ubuntu/Debian:

1.  Edit `weayoubot.service` (update paths to your directory).
2.  Copy to systemd:
    ```bash
    sudo cp weayoubot.service /etc/systemd/system/
    ```
3.  Enable and start:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable weayoubot
    sudo systemctl start weayoubot
    ```

## 📝 Usage

* `/start` - Initialize the bot.
* `/setup` - Configure weather subscription (City & Interval).
* `/settings` - Manage current subscription (Change City/Time or Unsubscribe).
* `/help` - Show instructions.

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
