import telebot
import requests
import json
import os
from dotenv import load_dotenv

# --- Настройки ---
load_dotenv()

TOKEN = os.getenv("WEATHER_BOT_TOKEN")  # Токен бота из .env файла
API_KEY = os.getenv("OPENWEATHER_API_KEY")  # API ключ для OpenWeatherMap из .env файла\

WEATHER_URL = f"https://api.openweathermap.org/data/2.5/weather?q={{city_name}}&appid={API_KEY}&units=metric"  # URL для получения погоды

BOT_PHOTO = "weather_bot_photo.png"  # Имя файла с фото бота
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Директория скрипта
CONTENT_DIR = os.path.join(SCRIPT_DIR, "content")  # Директория с контентом


if not TOKEN:
    raise ValueError(
        "Не установлена переменная окружения WEATHER_BOT_TOKEN. Создайте файл .env и добавьте в него WEATHER_BOT_TOKEN."
    )

if not API_KEY:
    raise ValueError(
        "Не установлена переменная окружения OPENWEATHER_API_KEY. Создайте файл .env и добавьте в него OPENWEATHER_API_KEY."
    )

bot = telebot.TeleBot(TOKEN)
chat_id = None  # Глобальная переменная для хранения chat_id


@bot.message_handler(commands=["start"])
def send_welcome(message):
    """
    Отправляет приветственное сообщение и фото бота.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.

    Returns:
        None
    """
    global chat_id
    chat_id = message.chat.id  # Сохраняем chat_id для использования в других местах

    try:
        with open(os.path.join(CONTENT_DIR, BOT_PHOTO), "rb") as photo:
            bot.send_photo(
                message.chat.id,
                photo,
                caption="Привет! Я Weather Bot. Отправь мне название города, и я пришлю тебе текущую погоду там.",
            )
    except Exception as e:
        bot.send_message(message.chat.id, f"Error loading bot photo: {e}")
        bot.send_message(
            message.chat.id,
            "Привет! Я Weather Bot. Отправь мне название города, и я пришлю тебе текущую погоду там.",
        )


@bot.message_handler(content_types=["text"])
def send_weather(message):
    """
    Отправляет текущую погоду для указанного города.

    Args:
        message (telebot.types.Message): Сообщение от пользователя.

    Returns:
        None
    """
    global chat_id
    chat_id = message.chat.id  # Сохраняем chat_id для использования в других местах
    city_name = message.text.strip()
    response = requests.get(WEATHER_URL.format(city_name=city_name))

    if response.status_code != 200:
        bot.reply_to(message, f"Не удалось получить погоду для города: {city_name}. Проверьте правильность названия.")
        return

    data = json.loads(response.text)
    bot.reply_to(message, f"Погода в {city_name}: {data['main']['temp']}°C")


if __name__ == "__main__":
    try:
        bot.infinity_polling()
        bot.send_message(chat_id, "Weather bot started")
    except Exception as e:
        if chat_id:
            bot.send_message(chat_id, f"Error initializing bot: {e}")
    except KeyboardInterrupt:
        if chat_id:
            bot.send_message(chat_id, "Weather bot stopped by user")
    finally:
        if chat_id:
            bot.send_message(chat_id, "Weather bot stopped")
