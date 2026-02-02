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
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Импорт локализации
from locales import get_text, get_wmo, TEXTS

# --- КОНФИГУРАЦИЯ ---
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DB_FILE = "weather_bot_v2.db"

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        chat_id INTEGER PRIMARY KEY,
        chat_type TEXT,
        lang_code TEXT,
        city_name TEXT,
        country_code TEXT,
        lat REAL,
        lon REAL,
        interval_hours INTEGER,
        target_hour INTEGER,
        last_run TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def save_subscription(data):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO subscriptions 
        (chat_id, chat_type, lang_code, city_name, country_code, lat, lon, interval_hours, target_hour, last_run)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['chat_id'], data['chat_type'], data['lang'], 
        data['city'], data['country'], data['lat'], data['lon'], 
        data['interval'], data.get('target_hour'), 
        datetime.now() - timedelta(days=1)
    ))
    conn.commit()
    conn.close()

def get_subscription(chat_id):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM subscriptions WHERE chat_id = ?", (chat_id,))
    row = cur.fetchone()
    conn.close()
    return row

def get_all_subscriptions():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM subscriptions")
    rows = cur.fetchall()
    conn.close()
    return rows

def delete_subscription(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM subscriptions WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

def update_last_run(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE subscriptions SET last_run = ? WHERE chat_id = ?", (datetime.now(), chat_id))
    conn.commit()
    conn.close()

# --- API ---
async def search_cities(city_name, lang_code):
    if lang_code not in ['ru', 'uk', 'en', 'de', 'fr', 'pl']: 
        lang_code = 'en'
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=10&language={lang_code}&format=json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            if "results" not in data: return []
            return data["results"]

async def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&wind_speed_unit=ms&timezone=auto"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return data["current"]

# --- СТЕЙТЫ И УТИЛИТЫ ---
class SetupState(StatesGroup):
    waiting_city_input = State()
    waiting_city_selection = State()
    waiting_interval = State()
    waiting_time = State()

router = Router()

def get_flag(country_code):
    if not country_code: return "🌍"
    return chr(127397 + ord(country_code[0])) + chr(127397 + ord(country_code[1]))

def get_user_lang(user: types.User):
    if not user or not user.language_code: return 'en'
    lang = user.language_code.split('-')[0]
    return lang if lang in TEXTS else 'en'

def check_admin(message: types.Message):
    # Хелпер для проверки прав
    pass # Реализовано внутри хендлеров

# --- ХЕНДЛЕРЫ ---

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    lang = get_user_lang(message.from_user)
    await message.answer(get_text(lang, "start"))

@router.message(Command("setup"))
async def cmd_setup(message: types.Message, state: FSMContext):
    # Проверка админа
    if message.chat.type in ['group', 'supergroup', 'channel']:
        admins = await message.bot.get_chat_administrators(message.chat.id)
        if message.from_user.id not in [a.user.id for a in admins]:
            await message.answer(get_text('en', "only_admin"))
            return
    
    lang = get_user_lang(message.from_user)
    await state.update_data(lang=lang, chat_id=message.chat.id, chat_type=message.chat.type)
    
    await state.set_state(SetupState.waiting_city_input)
    await message.answer(get_text(lang, "setup_start"))

# --- МЕНЮ НАСТРОЕК (/settings) ---
@router.message(Command("settings"))
async def cmd_settings(message: types.Message, state: FSMContext):
    # Проверка админа
    if message.chat.type in ['group', 'supergroup', 'channel']:
        admins = await message.bot.get_chat_administrators(message.chat.id)
        if message.from_user.id not in [a.user.id for a in admins]:
            await message.answer(get_text('en', "only_admin"))
            return

    sub = get_subscription(message.chat.id)
    lang = get_user_lang(message.from_user)

    if not sub:
        await message.answer(get_text(lang, "no_sub"))
        return

    # Формируем описание текущего режима
    if sub['interval_hours'] == 24:
        sched = f"Daily at {sub['target_hour']}:00"
    else:
        sched = f"Every {sub['interval_hours']} hours"

    text = get_text(lang, "settings_title", city=sub['city_name'], schedule=sched)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "btn_change_city"), callback_data="set_city")],
        [InlineKeyboardButton(text=get_text(lang, "btn_change_time"), callback_data="set_time")],
        [InlineKeyboardButton(text=get_text(lang, "btn_stop"), callback_data="set_stop")]
    ])
    
    await message.answer(text, reply_markup=kb, parse_mode="HTML")

# Обработка кнопок меню
@router.callback_query(F.data == "set_stop")
async def settings_stop(callback: CallbackQuery):
    lang = get_user_lang(callback.from_user)
    delete_subscription(callback.message.chat.id)
    await callback.message.edit_text(get_text(lang, "stop_success"))

@router.callback_query(F.data == "set_city")
async def settings_city(callback: CallbackQuery, state: FSMContext):
    lang = get_user_lang(callback.from_user)
    # Запускаем флоу настройки заново
    await state.update_data(lang=lang, chat_id=callback.message.chat.id, chat_type=callback.message.chat.type)
    await state.set_state(SetupState.waiting_city_input)
    await callback.message.edit_text(get_text(lang, "setup_start"))

@router.callback_query(F.data == "set_time")
async def settings_time(callback: CallbackQuery, state: FSMContext):
    # Загружаем текущие данные из БД в стейт, чтобы не потерять город
    sub = get_subscription(callback.message.chat.id)
    lang = get_user_lang(callback.from_user)
    
    if not sub:
        await callback.message.answer(get_text(lang, "no_sub"))
        return

    # Записываем старые данные о городе в память
    await state.update_data(
        lang=lang, 
        chat_id=sub['chat_id'], 
        chat_type=sub['chat_type'],
        city=sub['city_name'],
        country=sub['country_code'],
        lat=sub['lat'],
        lon=sub['lon']
    )

    # Показываем выбор времени сразу
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="2 h", callback_data="int_2"), InlineKeyboardButton(text="12 h", callback_data="int_12")],
        [InlineKeyboardButton(text="24 h (Daily)", callback_data="int_24")]
    ])
    
    await callback.message.edit_text(
        get_text(lang, "choose_interval", city=sub['city_name'], country=get_flag(sub['country_code'])),
        reply_markup=kb
    )
    await state.set_state(SetupState.waiting_interval)


# --- ЛОГИКА НАСТРОЙКИ (SETUP) ---

@router.message(SetupState.waiting_city_input)
async def process_city_search(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data['lang']
    
    cities = await search_cities(message.text, lang)
    
    if not cities:
        await message.answer(get_text(lang, "city_not_found"))
        return

    kb_builder = []
    for city in cities[:5]:
        flag = get_flag(city.get("country_code", "XX"))
        country = city.get("country", "")
        name = city.get("name", "")
        region = city.get("admin1", "")
        btn_text = f"{flag} {name}, {country}"
        if region: btn_text += f" ({region})"
        kb_builder.append([InlineKeyboardButton(text=btn_text, callback_data=f"city_{cities.index(city)}")])
    
    await state.update_data(cities_cache=cities)
    await message.answer(get_text(lang, "choose_city"), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_builder))
    await state.set_state(SetupState.waiting_city_selection)

@router.callback_query(SetupState.waiting_city_selection, F.data.startswith("city_"))
async def process_city_selection(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[1])
    data = await state.get_data()
    selected_city = data['cities_cache'][idx]
    
    await state.update_data(
        city=selected_city['name'],
        country=selected_city.get('country_code', 'XX'),
        lat=selected_city['latitude'],
        lon=selected_city['longitude']
    )
    
    lang = data['lang']
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="2 h", callback_data="int_2"), InlineKeyboardButton(text="12 h", callback_data="int_12")],
        [InlineKeyboardButton(text="24 h (Daily)", callback_data="int_24")]
    ])
    
    await callback.message.edit_text(
        get_text(lang, "choose_interval", city=selected_city['name'], country=selected_city.get('country', '')),
        reply_markup=kb
    )
    await state.set_state(SetupState.waiting_interval)

@router.callback_query(SetupState.waiting_interval, F.data.startswith("int_"))
async def process_interval_choice(callback: CallbackQuery, state: FSMContext):
    interval = int(callback.data.split("_")[1])
    await state.update_data(interval=interval)
    data = await state.get_data()
    lang = data['lang']

    if interval == 24:
        await callback.message.edit_text(get_text(lang, "ask_time"))
        await state.set_state(SetupState.waiting_time)
    else:
        save_subscription(data)
        await callback.message.edit_text(get_text(lang, "done_interval", city=data['city'], val=interval))
        await state.clear()

@router.message(SetupState.waiting_time)
async def process_time_input(message: types.Message, state: FSMContext):
    data = await state.get_data()
    lang = data['lang']
    try:
        hour = int(message.text)
        if not (0 <= hour <= 23): raise ValueError
    except ValueError:
        await message.answer(get_text(lang, "invalid_time"))
        return

    data['target_hour'] = hour
    save_subscription(data)
    await message.answer(get_text(lang, "done_daily", city=data['city'], val=hour))
    await state.clear()

# --- ПЛАНИРОВЩИК ---
async def sender_job(bot: Bot):
    subs = get_all_subscriptions()
    now = datetime.now()
    
    for sub in subs:
        should_send = False
        last_run = datetime.fromisoformat(sub['last_run']) if isinstance(sub['last_run'], str) else sub['last_run']
        
        if sub['interval_hours'] == 24:
            if now.hour == sub['target_hour'] and (now - last_run).total_seconds() > 3600 * 20:
                should_send = True
        else:
            if (now - last_run).total_seconds() >= sub['interval_hours'] * 3600:
                should_send = True

        if should_send:
            try:
                w = await get_weather(sub['lat'], sub['lon'])
                lang = sub['lang_code']
                msg = get_text(
                    lang, "weather_msg",
                    city=sub['city_name'],
                    country=get_flag(sub['country_code']),
                    desc=get_wmo(w['weather_code'], lang),
                    temp=w['temperature_2m'],
                    feels=w['apparent_temperature'],
                    wind=w['wind_speed_10m'],
                    hum=w['relative_humidity_2m']
                )
                await bot.send_message(sub['chat_id'], msg, parse_mode="HTML")
                update_last_run(sub['chat_id'])
            except Exception as e:
                logging.error(f"Error sending to {sub['chat_id']}: {e}")

async def main():
    init_db()
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(sender_job, "interval", minutes=1, kwargs={"bot": bot}) 
    scheduler.start()

    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())