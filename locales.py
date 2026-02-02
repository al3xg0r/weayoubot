# locales.py

TEXTS = {
    "en": {
        "start": "👋 Hi! I'm @WeaYouBot.\nI will send weather forecasts here.\n\nType /setup to start.",
        "setup_start": "🌍 Enter the **City Name** to search:",
        "city_not_found": "❌ City not found. Try again:",
        "choose_city": "✅ Found multiple locations. Please choose one:",
        "choose_interval": "⏱ How often should I send the weather for **{city}** ({country})?",
        "ask_time": "⏰ Enter the hour (0-23) for daily report (Server time):",
        "invalid_time": "❌ Invalid number. Enter 0-23.",
        "done_interval": "✅ Done! Weather for **{city}** every {val} hours.",
        "done_daily": "✅ Done! Weather for **{city}** daily at {val}:00.",
        "only_admin": "⚠️ Only admins can configure this bot.",
        "weather_msg": "🌡 <b>Weather in {city} ({country})</b>\n\n{desc}\nTemp: {temp}°C (Feels: {feels}°C)\nWind: {wind} m/s\nHumidity: {hum}%"
    },
    "ru": {
        "start": "👋 Привет! Я @WeaYouBot.\nЯ буду присылать погоду сюда по расписанию.\n\nЖми /setup для настройки.",
        "setup_start": "🌍 Введите **название города** для поиска:",
        "city_not_found": "❌ Город не найден. Попробуйте еще раз:",
        "choose_city": "✅ Найдено несколько мест. Выберите нужное:",
        "choose_interval": "⏱ Как часто присылать погоду для **{city}** ({country})?",
        "ask_time": "⏰ Введите час (0-23) для ежедневной рассылки:",
        "invalid_time": "❌ Неверное число. Введите от 0 до 23.",
        "done_interval": "✅ Готово! Погода для **{city}** каждые {val} ч.",
        "done_daily": "✅ Готово! Погода для **{city}** каждый день в {val}:00.",
        "only_admin": "⚠️ Только администраторы могут настраивать бота.",
        "weather_msg": "🌡 <b>Погода в {city} ({country})</b>\n\n{desc}\nТемп: {temp}°C (Ощущается: {feels}°C)\nВетер: {wind} м/с\nВлажность: {hum}%"
    },
    "uk": {
        "start": "👋 Привіт! Я @WeaYouBot.\nЯ надсилатиму сюди погоду за розкладом.\n\nТисни /setup для налаштування.",
        "setup_start": "🌍 Введіть **назву міста** для пошуку:",
        "city_not_found": "❌ Місто не знайдено. Спробуйте ще раз:",
        "choose_city": "✅ Знайдено декілька місць. Оберіть потрібне:",
        "choose_interval": "⏱ Як часто надсилати погоду для **{city}** ({country})?",
        "ask_time": "⏰ Введіть годину (0-23) для щоденної розсилки:",
        "invalid_time": "❌ Невірне число. Введіть від 0 до 23.",
        "done_interval": "✅ Готово! Погода для **{city}** кожні {val} год.",
        "done_daily": "✅ Готово! Погода для **{city}** щодня о {val}:00.",
        "only_admin": "⚠️ Тільки адміністратори можуть налаштовувати бота.",
        "weather_msg": "🌡 <b>Погода у {city} ({country})</b>\n\n{desc}\nТемп: {temp}°C (Відчувається: {feels}°C)\nВітер: {wind} м/с\nВологість: {hum}%"
    }
}

WEATHER_CODES = {
    0: {"en": "☀️ Clear sky", "ru": "☀️ Чистое небо", "uk": "☀️ Чисте небо"},
    1: {"en": "🌤 Mainly clear", "ru": "🌤 Преимущественно ясно", "uk": "🌤 Переважно ясно"},
    2: {"en": "⛅ Partly cloudy", "ru": "⛅ Переменная облачность", "uk": "⛅ Мінлива хмарність"},
    3: {"en": "☁️ Overcast", "ru": "☁️ Пасмурно", "uk": "☁️ Похмуро"},
    45: {"en": "🌫 Fog", "ru": "🌫 Туман", "uk": "🌫 Туман"},
    51: {"en": "🌧 Drizzle", "ru": "🌧 Морось", "uk": "🌧 Мряка"},
    61: {"en": "☔ Rain", "ru": "☔ Дождь", "uk": "☔ Дощ"},
    71: {"en": "❄️ Snow", "ru": "❄️ Снег", "uk": "❄️ Сніг"},
    95: {"en": "⛈ Thunderstorm", "ru": "⛈ Гроза", "uk": "⛈ Гроза"}
}

def get_text(lang, key, **kwargs):
    l = lang if lang in TEXTS else "en"
    return TEXTS[l][key].format(**kwargs)

def get_wmo(code, lang):
    l = lang if lang in TEXTS else "en"
    # Упрощенная логика для кодов, берем ближайший ключ
    code_map = code
    if code > 95: code_map = 95
    elif code >= 80: code_map = 61
    elif code >= 60: code_map = 61
    elif code >= 50: code_map = 51
    elif code >= 45: code_map = 45
    elif code >= 3: code_map = 3
    elif code >= 1: code_map = 1
    
    return WEATHER_CODES.get(code_map, WEATHER_CODES[0])[l]
