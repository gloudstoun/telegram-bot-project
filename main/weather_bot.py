import telebot
import requests
import os
import logging
from dotenv import load_dotenv

# --- Настройки логирования ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Загрузка переменных окружения ---
load_dotenv()

TOKEN = os.getenv("WEATHER_BOT_TOKEN")
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Проверка наличия необходимых переменных
if not TOKEN:
    raise ValueError(
        "Не установлена переменная окружения WEATHER_BOT_TOKEN. "
        "Создайте файл .env и добавьте в него WEATHER_BOT_TOKEN."
    )

if not API_KEY:
    raise ValueError(
        "Не установлена переменная окружения OPENWEATHER_API_KEY. "
        "Создайте файл .env и добавьте в него OPENWEATHER_API_KEY."
    )

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
BOT_PHOTO_PATH = "content/weather_bot_photo.png"

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    """Отправляет приветственное сообщение и фото бота."""
    logger.info(f"Пользователь {message.from_user.id} запустил бота")

    welcome_text = "Привет! Я Weather Bot. 🌤️\n" "Отправь мне название города, и я пришлю тебе текущую погоду там."

    try:
        if os.path.exists(BOT_PHOTO_PATH):
            with open(BOT_PHOTO_PATH, "rb") as photo:
                bot.send_photo(message.chat.id, photo, caption=welcome_text)
        else:
            bot.send_message(message.chat.id, welcome_text)
    except Exception as e:
        logger.error(f"Ошибка при отправке приветствия: {e}")
        bot.send_message(message.chat.id, welcome_text)


@bot.message_handler(content_types=["text"])
def send_weather(message):
    """Отправляет текущую погоду для указанного города."""
    city_name = message.text.strip()

    if not city_name:
        bot.reply_to(message, "Пожалуйста, введите название города.")
        return

    logger.info(f"Запрос погоды для города: {city_name}")

    try:
        # Параметры запроса
        params = {
            "q": city_name,
            "appid": API_KEY,
            "units": "metric",
            "lang": "ru",  # Для получения описания на русском языке
        }

        response = requests.get(WEATHER_URL, params=params, timeout=10)

        if response.status_code == 404:
            logger.warning(f"Город '{city_name}' не найден.")
            bot.reply_to(message, f"Город '{city_name}' не найден. Проверьте правильность названия.")
            return
        elif response.status_code != 200:
            logger.error(f"Ошибка API: {response.status_code}")
            bot.reply_to(message, "Произошла ошибка при получении данных о погоде. Попробуйте позже.")
            logger.error(f"API ошибка: {response.status_code}")
            return

        data = response.json()

        # Формируем красивый ответ
        weather_info = (
            f"🌍 Погода в городе {data['name']}, {data['sys']['country']}\n\n"
            f"🌡️ Температура: {data['main']['temp']:.1f}°C\n"
            f"🤔 Ощущается как: {data['main']['feels_like']:.1f}°C\n"
            f"📊 Влажность: {data['main']['humidity']}%\n"
            f"🌤️ Описание: {data['weather'][0]['description'].capitalize()}\n"
            f"💨 Скорость ветра: {data['wind'].get('speed', 'N/A')} м/с"
        )

        bot.reply_to(message, weather_info)
        logger.info(f"Отправлена погода для {city_name}")

    except requests.exceptions.Timeout:
        bot.reply_to(message, "Превышено время ожидания ответа. Попробуйте позже.")
    except requests.exceptions.RequestException as e:
        bot.reply_to(message, "Ошибка при запросе данных о погоде.")
        logger.error(f"Ошибка запроса: {e}")
    except KeyError as e:
        bot.reply_to(message, "Ошибка при обработке данных о погоде.")
        logger.error(f"Ключ не найден в ответе API: {e}")
    except Exception as e:
        bot.reply_to(message, "Произошла неожиданная ошибка.")
        logger.error(f"Неожиданная ошибка: {e}")


def main():
    """Основная функция для запуска бота."""
    logger.info("Запуск Weather Bot...")

    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
    finally:
        logger.info("Weather Bot остановлен")


if __name__ == "__main__":
    main()
