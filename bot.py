import asyncio
import logging
import sys
import os
import sqlite3
import aiohttp
from datetime import datetime, timedelta
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, StateFilter
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
        forecast_type TEXT DEFAULT 'current',
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
    ftype = data.get('forecast_type', 'current')
    
    cur.execute("""
        INSERT OR REPLACE INTO subscriptions 
        (chat_id, chat_type, lang_code, city_name, country_code, lat, lon, forecast_type, interval_hours, target_hour, last_run)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data['chat_id'], data['chat_type'], data['lang'], 
        data['city'], data['country'], data['lat'], data['lon'], 
        ftype,
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
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=5&language={lang_code}&format=json"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            if "results" not in data: return []
            return data["results"]

async def get_weather(lat, lon, mode='current'):
    if mode == 'daily':
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_sum,wind_speed_10m_max&current=temperature_2m,apparent_temperature&wind_speed_unit=ms&timezone=auto&forecast_days=1"
    elif mode == 'weekly':
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=weather_code,temperature_2m_max,temperature_2m_min&timezone=auto&forecast_days=7"
    else:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m&wind_speed_unit=ms&timezone=auto"
        
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            if mode in ['daily', 'weekly']:
                return data
            else:
                return data.get('current')

# --- СТЕЙТЫ И УТИЛИТЫ ---
class SetupState(StatesGroup):
    waiting_city_input = State()
    waiting_city_selection = State()
    waiting_forecast_type = State()
    waiting_interval = State()
    waiting_time = State()

class OneTimeState(StatesGroup):
    waiting_city_selection = State()
    waiting_forecast_type = State()

router = Router()

def get_flag(country_code):
    if not country_code: return "🌍"
    return chr(127397 + ord(country_code[0])) + chr(127397 + ord(country_code[1]))

def get_user_lang(user: types.User):
    if not user or not user.language_code: return 'en'
    lang = user.language_code.split('-')[0]
    return lang if lang in TEXTS else 'en'

# --- ХЕНДЛЕРЫ КОМАНД ---

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    lang = get_user_lang(message.from_user)
    await message.answer(get_text(lang, "start"))

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    lang = get_user_lang(message.from_user)
    await message.answer(get_text(lang, "help_text"))

@router.message(Command("setup"))
async def cmd_setup(message: types.Message, state: FSMContext):
    if message.chat.type in ['group', 'supergroup', 'channel']:
        admins = await message.bot.get_chat_administrators(message.chat.id)
        if message.from_user.id not in [a.user.id for a in admins]:
            await message.answer(get_text('en', "only_admin"))
            return
    
    lang = get_user_lang(message.from_user)
    await state.update_data(lang=lang, chat_id=message.chat.id, chat_type=message.chat.type)
    
    await state.set_state(SetupState.waiting_city_input)
    await message.answer(get_text(lang, "setup_start"))

# --- ОБРАБОТКА ТЕКСТА (РАЗОВЫЙ ЗАПРОС) ---
@router.message(F.text & ~F.text.startswith("/"), StateFilter(None))
async def process_text_search(message: types.Message, state: FSMContext):
    lang = get_user_lang(message.from_user)
    cities = await search_cities(message.text, lang)
    
    if not cities:
        if message.chat.type == 'private':
            await message.answer(get_text(lang, "city_not_found"))
        return

    await state.update_data(lang=lang, cities_cache=cities)
    
    kb_builder = []
    for city in cities[:5]:
        flag = get_flag(city.get("country_code", "XX"))
        country = city.get("country", "")
        name = city.get("name", "")
        region = city.get("admin1", "")
        btn_text = f"{flag} {name}, {country}"
        if region: btn_text += f" ({region})"
        kb_builder.append([InlineKeyboardButton(text=btn_text, callback_data=f"ot_city_{cities.index(city)}")])
    
    await message.answer(get_text(lang, "choose_city"), reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_builder))
    await state.set_state(OneTimeState.waiting_city_selection)

# --- ЛОГИКА РАЗОВОГО ЗАПРОСА (ONE TIME) ---

@router.callback_query(OneTimeState.waiting_city_selection, F.data.startswith("ot_city_"))
async def process_onetime_city(callback: CallbackQuery, state: FSMContext):
    idx = int(callback.data.split("_")[2])
    data = await state.get_data()
    selected_city = data['cities_cache'][idx]
    
    await state.update_data(
        city=selected_city['name'],
        country=selected_city.get('country_code', 'XX'),
        lat=selected_city['latitude'],
        lon=selected_city['longitude']
    )
    
    lang = data['lang']
    # В разовом запросе ОСТАВЛЯЕМ 3 кнопки
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "btn_current"), callback_data="ot_type_current")],
        [InlineKeyboardButton(text=get_text(lang, "btn_daily"), callback_data="ot_type_daily")],
        [InlineKeyboardButton(text=get_text(lang, "btn_weekly"), callback_data="ot_type_weekly")]
    ])
    
    await callback.message.edit_text(get_text(lang, "choose_type_once"), reply_markup=kb)
    await state.set_state(OneTimeState.waiting_forecast_type)

@router.callback_query(OneTimeState.waiting_forecast_type, F.data.startswith("ot_type_"))
async def process_onetime_result(callback: CallbackQuery, state: FSMContext):
    ftype = callback.data.split("_")[2]
    data = await state.get_data()
    lang = data['lang']
    
    try:
        w = await get_weather(data['lat'], data['lon'], ftype)
        
        if ftype == 'daily':
            daily = w['daily']
            curr = w['current']
            msg = get_text(
                lang, "daily_msg",
                city=data['city'],
                country=get_flag(data['country']),
                desc=get_wmo(daily['weather_code'][0], lang),
                t_now=curr['temperature_2m'],
                t_feels=curr['apparent_temperature'],
                t_max=daily['temperature_2m_max'][0],
                t_min=daily['temperature_2m_min'][0],
                rain=daily['precipitation_sum'][0],
                wind=daily['wind_speed_10m_max'][0],
                sunrise=daily['sunrise'][0].split('T')[1],
                sunset=daily['sunset'][0].split('T')[1]
            )
        elif ftype == 'weekly':
            daily = w['daily']
            lines = []
            for i in range(7):
                dt = datetime.strptime(daily['time'][i], "%Y-%m-%d")
                short_date = dt.strftime("%d.%m")
                w_code = daily['weather_code'][i]
                t_max = daily['temperature_2m_max'][i]
                t_min = daily['temperature_2m_min'][i]
                
                desc_full = get_wmo(w_code, lang)
                emoji = desc_full.split()[0]
                
                lines.append(f"▪️ {short_date}: {emoji} <b>{t_min}°C</b> … <b>{t_max}°C</b>")
            
            msg = get_text(
                lang, "weekly_msg",
                city=data['city'],
                country=get_flag(data['country']),
                forecast_text="\n".join(lines)
            )
        else:
            msg = get_text(
                lang, "weather_msg",
                city=data['city'],
                country=get_flag(data['country']),
                desc=get_wmo(w['weather_code'], lang),
                temp=w['temperature_2m'],
                feels=w['apparent_temperature'],
                wind=w['wind_speed_10m'],
                hum=w['relative_humidity_2m']
            )
        
        await callback.message.edit_text(msg)
    except Exception as e:
        logging.error(f"Error in onetime: {e}")
        await callback.message.edit_text("⚠️ Error fetching weather.")
    
    await state.clear()


# --- НАСТРОЙКИ И SETUP ---
@router.message(Command("settings"))
async def cmd_settings(message: types.Message, state: FSMContext):
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

    if sub['interval_hours'] == 24:
        sched = f"Daily at {sub['target_hour']}:00"
    else:
        sched = f"Every {sub['interval_hours']} hours"
    
    ftype = sub['forecast_type'] if 'forecast_type' in sub.keys() else 'current'
    
    if ftype == 'daily':
        type_display = get_text(lang, "btn_daily")
    elif ftype == 'weekly':
        type_display = get_text(lang, "btn_weekly")
    else:
        type_display = get_text(lang, "btn_current")

    text = get_text(lang, "settings_title", city=sub['city_name'], type=type_display, schedule=sched)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "btn_change_city"), callback_data="set_city")],
        [InlineKeyboardButton(text=get_text(lang, "btn_change_time"), callback_data="set_time")],
        [InlineKeyboardButton(text=get_text(lang, "btn_stop"), callback_data="set_stop")]
    ])
    
    await message.answer(text, reply_markup=kb)

@router.callback_query(F.data == "set_stop")
async def settings_stop(callback: CallbackQuery):
    lang = get_user_lang(callback.from_user)
    delete_subscription(callback.message.chat.id)
    await callback.message.edit_text(get_text(lang, "stop_success"))

@router.callback_query(F.data == "set_city")
async def settings_city(callback: CallbackQuery, state: FSMContext):
    lang = get_user_lang(callback.from_user)
    await state.update_data(lang=lang, chat_id=callback.message.chat.id, chat_type=callback.message.chat.type)
    await state.set_state(SetupState.waiting_city_input)
    await callback.message.edit_text(get_text(lang, "setup_start"))

@router.callback_query(F.data == "set_time")
async def settings_time(callback: CallbackQuery, state: FSMContext):
    sub = get_subscription(callback.message.chat.id)
    lang = get_user_lang(callback.from_user)
    
    if not sub:
        await callback.message.answer(get_text(lang, "no_sub"))
        return

    await state.update_data(
        lang=lang, 
        chat_id=sub['chat_id'], 
        chat_type=sub['chat_type'],
        city=sub['city_name'],
        country=sub['country_code'],
        lat=sub['lat'],
        lon=sub['lon'],
        forecast_type=sub['forecast_type']
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="2 h", callback_data="int_2"), InlineKeyboardButton(text="12 h", callback_data="int_12")],
        [InlineKeyboardButton(text="24 h (Daily)", callback_data="int_24")]
    ])
    
    await callback.message.edit_text(
        get_text(lang, "choose_interval", city=sub['city_name'], country=get_flag(sub['country_code'])),
        reply_markup=kb
    )
    await state.set_state(SetupState.waiting_interval)

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
    
    # ИЗМЕНЕНИЕ: В настройках ПОДПИСКИ теперь только 2 кнопки
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(lang, "btn_current"), callback_data="type_current")],
        [InlineKeyboardButton(text=get_text(lang, "btn_daily"), callback_data="type_daily")]
    ])
    
    await callback.message.edit_text(get_text(lang, "choose_type_sub"), reply_markup=kb)
    await state.set_state(SetupState.waiting_forecast_type)

@router.callback_query(SetupState.waiting_forecast_type, F.data.startswith("type_"))
async def process_forecast_type(callback: CallbackQuery, state: FSMContext):
    ftype = callback.data.split("_")[1]
    await state.update_data(forecast_type=ftype)
    
    data = await state.get_data()
    lang = data['lang']
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="2 h", callback_data="int_2"), InlineKeyboardButton(text="12 h", callback_data="int_12")],
        [InlineKeyboardButton(text="24 h (Daily)", callback_data="int_24")]
    ])
    
    await callback.message.edit_text(
        get_text(lang, "choose_interval", city=data['city'], country=get_flag(data['country'])),
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
                lang = sub['lang_code']
                ftype = sub['forecast_type']
                w = await get_weather(sub['lat'], sub['lon'], ftype)
                
                if ftype == 'daily':
                    daily = w['daily']
                    curr = w['current']
                    msg = get_text(
                        lang, "daily_msg",
                        city=sub['city_name'],
                        country=get_flag(sub['country_code']),
                        desc=get_wmo(daily['weather_code'][0], lang),
                        t_now=curr['temperature_2m'],
                        t_feels=curr['apparent_temperature'],
                        t_max=daily['temperature_2m_max'][0],
                        t_min=daily['temperature_2m_min'][0],
                        rain=daily['precipitation_sum'][0],
                        wind=daily['wind_speed_10m_max'][0],
                        sunrise=daily['sunrise'][0].split('T')[1],
                        sunset=daily['sunset'][0].split('T')[1]
                    )
                elif ftype == 'weekly':
                    daily = w['daily']
                    lines = []
                    for i in range(7):
                        dt = datetime.strptime(daily['time'][i], "%Y-%m-%d")
                        short_date = dt.strftime("%d.%m")
                        w_code = daily['weather_code'][i]
                        t_max = daily['temperature_2m_max'][i]
                        t_min = daily['temperature_2m_min'][i]
                        
                        desc_full = get_wmo(w_code, lang)
                        emoji = desc_full.split()[0]
                        
                        lines.append(f"▪️ {short_date}: {emoji} <b>{t_min}°C</b> … <b>{t_max}°C</b>")
                    
                    msg = get_text(
                        lang, "weekly_msg",
                        city=sub['city_name'],
                        country=get_flag(sub['country_code']),
                        forecast_text="\n".join(lines)
                    )
                else:
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
                await bot.send_message(sub['chat_id'], msg)
                update_last_run(sub['chat_id'])
            except Exception as e:
                logging.error(f"Error sending to {sub['chat_id']}: {e}")

async def main():
    init_db()
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
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