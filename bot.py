import asyncio
import logging
import sys
import os
import sqlite3
import aiohttp
from datetime import datetime, timedelta
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- КОНФИГУРАЦИЯ ---
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DB_FILE = "weather_bot.db"

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        chat_id INTEGER PRIMARY KEY,
        chat_type TEXT,
        city_name TEXT,
        lat REAL,
        lon REAL,
        interval_hours INTEGER,
        target_hour INTEGER,
        last_run TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def save_subscription(chat_id, chat_type, city, lat, lon, interval, target_hour=None):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # Если подписка уже есть — обновляем
    cur.execute("""
        INSERT OR REPLACE INTO subscriptions (chat_id, chat_type, city_name, lat, lon, interval_hours, target_hour, last_run)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (chat_id, chat_type, city, lat, lon, interval, target_hour, datetime.now() - timedelta(days=1)))
    conn.commit()
    conn.close()

def get_subscriptions():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM subscriptions")
    rows = cur.fetchall()
    conn.close()
    return rows

def update_last_run(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE subscriptions SET last_run = ? WHERE chat_id = ?", (datetime.now(), chat_id))
    conn.commit()
    conn.close()

# --- ВНЕШНИЕ API ---
async def get_coordinates(city_name):
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=ru&format=json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            if "results" in data:
                return data["results"][0]["latitude"], data["results"][0]["longitude"], data["results"][0]["name"]
            return None, None, None

async def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&wind_speed_unit=ms&timezone=auto"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return data["current"]

def decode_wmo(code):
    # Упрощенная расшифровка кодов погоды WMO
    if code == 0: return "☀️ Чистое небо"
    if 1 <= code <= 3: return "🌤 Переменная облачность"
    if 45 <= code <= 48: return "🌫 Туман"
    if 51 <= code <= 67: return "🌧 Дождь"
    if 71 <= code <= 77: return "❄️ Снег"
    if 80 <= code <= 82: return "🌦 Ливень"
    if 95 <= code <= 99: return "⛈ Гроза"
    return "unknown"

# --- ЛОГИКА БОТА ---
router = Router()

class SetupState(StatesGroup):
    waiting_city = State()
    waiting_interval = State()
    waiting_time = State() # Только для интервала 24ч

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я @WeaYouBot.\n"
        "Я буду присылать погоду в этот чат по расписанию.\n\n"
        "Нажмите /setup чтобы настроить рассылку."
    )

@router.message(Command("setup"))
async def cmd_setup(message: types.Message, state: FSMContext):
    # Проверка прав админа в группах
    if message.chat.type in ['group', 'supergroup']:
        admins = await message.bot.get_chat_administrators(message.chat.id)
        if message.from_user.id not in [a.user.id for a in admins]:
            await message.answer("Только администраторы могут настраивать бота.")
            return

    await state.set_state(SetupState.waiting_city)
    await message.answer("🌍 Введите название города (например: Москва):")

@router.message(SetupState.waiting_city)
async def process_city(message: types.Message, state: FSMContext):
    lat, lon, city_real = await get_coordinates(message.text)
    if not lat:
        await message.answer("❌ Город не найден. Попробуйте еще раз:")
        return

    await state.update_data(city=city_real, lat=lat, lon=lon)
    
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="2 часа"), KeyboardButton(text="12 часов")],
        [KeyboardButton(text="24 часа")]
    ], resize_keyboard=True, one_time_keyboard=True)
    
    await state.set_state(SetupState.waiting_interval)
    await message.answer(f"✅ Город найден: {city_real}.\nКак часто присылать погоду?", reply_markup=kb)

@router.message(SetupState.waiting_interval)
async def process_interval(message: types.Message, state: FSMContext):
    text = message.text.lower()
    
    if "2 часа" in text:
        interval = 2
    elif "12 часов" in text:
        interval = 12
    elif "24 часа" in text:
        interval = 24
        await state.update_data(interval=interval)
        await state.set_state(SetupState.waiting_time)
        await message.answer("⏰ Введите час отправки (от 0 до 23, например: 9):", reply_markup=ReplyKeyboardRemove())
        return
    else:
        await message.answer("Используйте кнопки меню.")
        return

    data = await state.get_data()
    save_subscription(message.chat.id, message.chat.type, data['city'], data['lat'], data['lon'], interval)
    await state.clear()
    await message.answer(f"✅ Готово! Буду слать погоду для {data['city']} каждые {interval} ч.", reply_markup=ReplyKeyboardRemove())

@router.message(SetupState.waiting_time)
async def process_time(message: types.Message, state: FSMContext):
    try:
        hour = int(message.text)
        if not (0 <= hour <= 23): raise ValueError
    except ValueError:
        await message.answer("❌ Введите число от 0 до 23.")
        return

    data = await state.get_data()
    save_subscription(message.chat.id, message.chat.type, data['city'], data['lat'], data['lon'], 24, target_hour=hour)
    await state.clear()
    await message.answer(f"✅ Готово! Погода для {data['city']} каждый день в {hour}:00.", reply_markup=ReplyKeyboardRemove())

# --- ПЛАНИРОВЩИК ---
async def sender_job(bot: Bot):
    subs = get_subscriptions()
    now = datetime.now()
    
    for sub in subs:
        chat_id = sub['chat_id']
        city = sub['city_name']
        interval = sub['interval_hours']
        target_hour = sub['target_hour']
        last_run = datetime.fromisoformat(sub['last_run']) if isinstance(sub['last_run'], str) else sub['last_run']

        should_send = False
        
        # Логика 24 часов (по конкретному времени)
        if interval == 24:
            if now.hour == target_hour and (now - last_run).total_seconds() > 3600 * 20:
                should_send = True
        # Логика интервалов (2 или 12 часов)
        else:
            if (now - last_run).total_seconds() >= interval * 3600:
                should_send = True

        if should_send:
            try:
                weather = await get_weather(sub['lat'], sub['lon'])
                msg = (
                    f"🌡 <b>Погода в {city}</b>\n"
                    f"{decode_wmo(weather['weather_code'])}\n"
                    f"Температура: {weather['temperature_2m']}°C (Ощущается: {weather['apparent_temperature']}°C)\n"
                    f"Ветер: {weather['wind_speed_10m']} м/с\n"
                    f"Влажность: {weather['relative_humidity_2m']}%"
                )
                await bot.send_message(chat_id, msg, parse_mode="HTML")
                update_last_run(chat_id)
            except Exception as e:
                logging.error(f"Error sending to {chat_id}: {e}")

async def main():
    init_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    # Запуск планировщика
    scheduler = AsyncIOScheduler()
    # Проверяем базу каждую минуту
    scheduler.add_job(sender_job, "interval", minutes=1, kwargs={"bot": bot}) 
    scheduler.start()

    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
