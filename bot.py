import asyncio
import csv
from datetime import datetime
from os.path import exists

import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from secret import token

API_TOKEN = token[0]
LOG_FILE = 'user_log.csv'

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Клавиатура
keyboard = ReplyKeyboardBuilder()
keyboard.add(
    KeyboardButton(text="Финансы"),
    KeyboardButton(text="Гео"),
    KeyboardButton(text="Погода")
)
keyboard.adjust(2)

def log_action(user_id, username, motion, api, api_answer):
    now = datetime.now()
    file_exists = exists(LOG_FILE)

    # Определяем номер лога
    if file_exists:
        with open(LOG_FILE, mode='r', encoding='utf-8') as f:
            log_number = sum(1 for _ in f)
    else:
        log_number = 1  # первая строка будет заголовком, следующая — первая запись

    row = [
        log_number,
        user_id,
        username or 'NONE',
        motion,
        api,
        now.strftime("%Y-%m-%d"),
        now.strftime("%H:%M:%S"),
        api_answer
    ]

    with open(LOG_FILE, mode='a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Unic_ID", "User_ID", "TG_nick", "Motion", "API", "Date", "Time", "API_answer"])
        writer.writerow(row)
# /start
@dp.message(Command("start"))
async def start_handler(message: Message):
    log_action(message.from_user.id, message.from_user.username, "Command", "NONE", "NONE")
    await message.answer("Выберите API:", reply_markup=keyboard.as_markup(resize_keyboard=True))

# Обработка кнопок
@dp.message(F.text.in_(["Финансы", "Гео", "Погода"]))
async def api_handler(message: Message):
    api_name = ""
    api_answer = ""

    async with aiohttp.ClientSession() as session:
        if message.text == "Финансы":
            api_name = "CBR"
            async with session.get("https://www.cbr-xml-daily.ru/daily_json.js") as resp:
                data = await resp.json()
                usd = data.get("Valute", {}).get("USD", {}).get("Value", "нет данных")
                api_answer = f"{usd} RUB"
                await message.answer(f"Курс доллара: {api_answer}")

        elif message.text == "Гео":
            api_name = "OpenStreetMap"
            async with session.get("https://nominatim.openstreetmap.org/search?format=json&q=Гродно") as resp:
                data = await resp.json()
                if data:
                    lat = data[0]["lat"]
                    lon = data[0]["lon"]
                    api_answer = f"{lat}, {lon}"
                    await message.answer(f"Координаты Гродно: {api_answer}")
                else:
                    api_answer = "нет данных"
                    await message.answer("Не удалось найти координаты.")

        elif message.text == "Погода":
            api_name = "Open-Meteo"
            async with session.get("https://api.open-meteo.com/v1/forecast?latitude=53.68&longitude=23.83&current_weather=true") as resp:
                data = await resp.json()
                weather = data.get("current_weather", {})
                temp = weather.get("temperature", "нет данных")
                wind = weather.get("windspeed", "нет данных")
                api_answer = f"{temp}°C, ветер {wind} км/ч"
                await message.answer(f"Погода в Гродно: {api_answer}")

    log_action(message.from_user.id, message.from_user.username, "Button press", api_name, api_answer)

# Эхо
@dp.message()
async def echo_handler(message: Message):
    log_action(message.from_user.id, message.from_user.username, "Keyboard typing", "NONE", "NONE")
    await message.answer(f"Вы написали: {message.text}")

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

