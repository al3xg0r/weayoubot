# locales.py

TEXTS = {
    "en": {
        "start": "👋 Hi! I'm @WeaYouBot (Your Weather Bot).\nI will send weather forecasts here.\n\nType /setup to start or /help for instructions.",
        "setup_start": "🌍 Enter the **City Name** to search:",
        "city_not_found": "❌ City not found. Try again:",
        "choose_city": "✅ Found multiple locations. Please choose one:",
        "choose_type": "📊 **What kind of report do you want?**\n\n🔹 **Current**: What's happening right now.\n🔸 **Daily**: Full forecast for today (Max/Min, Rain).",
        "btn_current": "🔹 Current Weather",
        "btn_daily": "🔸 Daily Forecast",
        
        "choose_interval": "⏱ How often should I send the weather for **{city}** ({country})?",
        "ask_time": "⏰ Enter the hour (0-23) for daily report:",
        "invalid_time": "❌ Invalid number. Enter 0-23.",
        "done_interval": "✅ Done! Weather for **{city}** every {val} hours.",
        "done_daily": "✅ Done! Weather for **{city}** daily at {val}:00.",
        "only_admin": "⚠️ Only admins can configure this bot.",
        
        "weather_msg": "🌡 <b>Current in {city} ({country})</b>\n\n{desc}\nTemp: {temp}°C (Feels: {feels}°C)\nWind: {wind} m/s\nHumidity: {hum}%",
        
        # Обновленный шаблон (EN)
        "daily_msg": "📅 <b>{city} ({country})</b>\n\n🌡 Now: <b>{t_now}°C</b>\n\nToday:\n{desc} (Rain: {rain} mm)\n🌡 Temp: <b>{t_max}°C</b> - <b>{t_min}°C</b>\n💨 Wind (max): {wind} m/s\n🌅 Rise: {sunrise} | 🌇 Set: {sunset}",

        "settings_title": "⚙️ <b>Settings</b>\n\n📍 City: <b>{city}</b>\n📊 Type: <b>{type}</b>\n🕒 Schedule: <b>{schedule}</b>",
        "btn_change_city": "🌍 Change City",
        "btn_change_time": "⏰ Change Schedule",
        "btn_stop": "🛑 Unsubscribe",
        "stop_success": "✅ Subscription stopped.",
        "no_sub": "❌ You don't have an active subscription. Type /setup.",
        "help_text": "📚 <b>Help & Instructions</b>\n\n<b>Commands:</b>\n/start - Restart\n/setup - Subscribe to weather\n/settings - Manage subscription\n/help - Show this message\n\n<b>👥 How to use in Groups/Channels:</b>\n1. Add bot to the group.\n2. <b>Make it an Admin</b> (required to see messages).\n3. Type /setup in the chat."
    },
    "ru": {
        "start": "👋 Привет! Я @WeaYouBot (Your Weather Bot).\nЯ буду присылать погоду сюда по расписанию.\n\nЖми /setup для настройки или /help для помощи.",
        "setup_start": "🌍 Введите **название города** для поиска:",
        "city_not_found": "❌ Город не найден. Попробуйте еще раз:",
        "choose_city": "✅ Найдено несколько мест. Выберите нужное:",
        "choose_type": "📊 **Какой прогноз присылать?**\n\n🔹 **Текущий**: Погода прямо сейчас.\n🔸 **На день**: Прогноз на сегодня (Макс/Мин, Осадки).",
        "btn_current": "🔹 Текущая погода",
        "btn_daily": "🔸 Прогноз на день",

        "choose_interval": "⏱ Как часто присылать погоду для **{city}** ({country})?",
        "ask_time": "⏰ Введите час (0-23) для ежедневной рассылки:",
        "invalid_time": "❌ Неверное число. Введите от 0 до 23.",
        "done_interval": "✅ Готово! Погода для **{city}** каждые {val} ч.",
        "done_daily": "✅ Готово! Погода для **{city}** каждый день в {val}:00.",
        "only_admin": "⚠️ Только администраторы могут настраивать бота.",
        
        "weather_msg": "🌡 <b>Сейчас в {city} ({country})</b>\n\n{desc}\nТемп: {temp}°C (Ощущается: {feels}°C)\nВетер: {wind} м/с\nВлажность: {hum}%",
        
        # Обновленный шаблон (RU)
        "daily_msg": "📅 <b>{city} ({country})</b>\n\n🌡 Сейчас: <b>{t_now}°C</b>\n\nСегодня:\n{desc} (Осадки: {rain} мм)\n🌡 Температура <b>{t_max}°C</b> - <b>{t_min}°C</b>\n💨 Ветер (макс): {wind} м/с\n🌅 Восход: {sunrise} | 🌇 Закат: {sunset}",

        "settings_title": "⚙️ <b>Настройки</b>\n\n📍 Город: <b>{city}</b>\n📊 Тип: <b>{type}</b>\n🕒 Расписание: <b>{schedule}</b>",
        "btn_change_city": "🌍 Изменить город",
        "btn_change_time": "⏰ Изменить время",
        "btn_stop": "🛑 Отключить рассылку",
        "stop_success": "✅ Подписка отключена.",
        "no_sub": "❌ У вас нет активной подписки. Нажмите /setup.",
        "help_text": "📚 <b>Помощь и Инструкция</b>\n\n<b>Команды:</b>\n/start - Старт\n/setup - Настроить погоду\n/settings - Управление подпиской\n/help - Показать это сообщение\n\n<b>👥 Как использовать в Группах/Каналах:</b>\n1. Добавьте бота в чат.\n2. <b>Сделайте его Админом</b> (обязательно).\n3. Напишите /setup в чате."
    },
    "uk": {
        "start": "👋 Привіт! Я @WeaYouBot (Your Weather Bot).\nЯ надсилатиму сюди погоду за розкладом.\n\nТисни /setup для налаштування або /help для довідки.",
        "setup_start": "🌍 Введіть **назву міста** для пошуку:",
        "city_not_found": "❌ Місто не знайдено. Спробуйте ще раз:",
        "choose_city": "✅ Знайдено декілька місць. Оберіть потрібне:",
        "choose_type": "📊 **Який прогноз надсилати?**\n\n🔹 **Поточний**: Погода прямо зараз.\n🔸 **На день**: Прогноз на сьогодні (Макс/Мін, Опади).",
        "btn_current": "🔹 Поточна погода",
        "btn_daily": "🔸 Прогноз на день",

        "choose_interval": "⏱ Як часто надсилати погоду для **{city}** ({country})?",
        "ask_time": "⏰ Введіть годину (0-23) для щоденної розсилки:",
        "invalid_time": "❌ Невірне число. Введіть від 0 до 23.",
        "done_interval": "✅ Готово! Погода для **{city}** кожні {val} год.",
        "done_daily": "✅ Готово! Погода для **{city}** щодня о {val}:00.",
        "only_admin": "⚠️ Тільки адміністратори можуть налаштовувати бота.",
        
        "weather_msg": "🌡 <b>Зараз у {city} ({country})</b>\n\n{desc}\nТемп: {temp}°C (Відчувається: {feels}°C)\nВітер: {wind} м/с\nВологість: {hum}%",
        
        # Обновленный шаблон (UK)
        "daily_msg": "📅 <b>{city} ({country})</b>\n\n🌡 Зараз: <b>{t_now}°C</b>\n\nСьогодні:\n{desc} (Опади: {rain} мм)\n🌡 Температура <b>{t_max}°C</b> - <b>{t_min}°C</b>\n💨 Вітер (макс): {wind} м/с\n🌅 Схід: {sunrise} | 🌇 Захід: {sunset}",

        "settings_title": "⚙️ <b>Налаштування</b>\n\n📍 Місто: <b>{city}</b>\n📊 Тип: <b>{type}</b>\n🕒 Розклад: <b>{schedule}</b>",
        "btn_change_city": "🌍 Змінити місто",
        "btn_change_time": "⏰ Змінити час",
        "btn_stop": "🛑 Відписатися",
        "stop_success": "✅ Підписку скасовано.",
        "no_sub": "❌ У вас немає активної підписки. Натисніть /setup.",
        "help_text": "📚 <b>Довідка та Інструкція</b>\n\n<b>Команди:</b>\n/start - Старт\n/setup - Налаштувати погоду\n/settings - Керування підпискою\n/help - Показати це повідомлення\n\n<b>👥 Як використовувати в Групах/Каналах:</b>\n1. Додайте бота в чат.\n2. <b>Зробіть його Адміном</b> (обов'язково).\n3. Напишіть /setup у чаті."
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
    code_map = code
    if code > 95: code_map = 95
    elif code >= 80: code_map = 61
    elif code >= 60: code_map = 61
    elif code >= 50: code_map = 51
    elif code >= 45: code_map = 45
    elif code >= 3: code_map = 3
    elif code >= 1: code_map = 1
    return WEATHER_CODES.get(code_map, WEATHER_CODES[0])[l]