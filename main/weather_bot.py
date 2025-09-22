import telebot
import requests
import os
import logging
from dotenv import load_dotenv

# --- Logging setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load environment variables ---
load_dotenv()

TOKEN = os.getenv("WEATHER_BOT_TOKEN")
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Check for required environment variables
if not TOKEN:
    raise ValueError("WEATHER_BOT_TOKEN environment variable not set. " "Create a .env file and add WEATHER_BOT_TOKEN.")

if not API_KEY:
    raise ValueError(
        "OPENWEATHER_API_KEY environment variable not set. " "Create a .env file and add OPENWEATHER_API_KEY."
    )

WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
BOT_PHOTO_PATH = "content/weather_bot_photo.png"

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=["start"])
def send_welcome(message):
    """Sends a welcome message and a bot photo."""
    logger.info(f"User {message.from_user.id} started the bot.")

    welcome_text = "Hello! I'm Weather Bot. 🌤️\n" "Send me a city name, and I'll send you the current weather there."

    try:
        if os.path.exists(BOT_PHOTO_PATH):
            with open(BOT_PHOTO_PATH, "rb") as photo:
                bot.send_photo(message.chat.id, photo, caption=welcome_text)
        else:
            bot.send_message(message.chat.id, welcome_text)
    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")
        bot.send_message(message.chat.id, welcome_text)


@bot.message_handler(content_types=["text"])
def send_weather(message):
    """Sends the current weather for the specified city."""
    city_name = message.text.strip()

    if not city_name:
        bot.reply_to(message, "Please enter a city name.")
        return

    logger.info(f"Weather request for city: {city_name}")

    try:
        # Request parameters
        params = {
            "q": city_name,
            "appid": API_KEY,
            "units": "metric",
            "lang": "en",
        }

        response = requests.get(WEATHER_URL, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Format the beautiful response
        weather_info = (
            f"🌍 Weather in {data['name']}, {data['sys']['country']}\n\n"
            f"🌡️ Temperature: {data['main']['temp']:.1f}°C\n"
            f"🤔 Feels like: {data['main']['feels_like']:.1f}°C\n"
            f"📊 Humidity: {data['main']['humidity']}%\n"
            f"🌤️ Description: {data['weather'][0]['description'].capitalize()}\n"
            f"💨 Wind speed: {data['wind'].get('speed', 'N/A')} m/s"
        )

        bot.reply_to(message, weather_info)
        logger.info(f"Weather sent for {city_name}")

    except requests.exceptions.HTTPError as http_err:
        if http_err.response.status_code == 404:
            logger.warning(f"City '{city_name}' not found.")
            bot.reply_to(message, f"City '{city_name}' not found. Please check the spelling.")
        else:
            logger.error(f"HTTP error: {http_err}")
            bot.reply_to(message, "An error occurred while fetching weather data. Please try again later.")
    except requests.exceptions.Timeout:
        bot.reply_to(message, "The request timed out. Please try again later.")
    except requests.exceptions.RequestException as e:
        bot.reply_to(message, "An error occurred during the weather data request.")
        logger.error(f"Request error: {e}")
    except KeyError as e:
        bot.reply_to(message, "An error occurred while processing weather data.")
        logger.error(f"Key not found in API response: {e}")
    except Exception as e:
        bot.reply_to(message, "An unexpected error occurred.")
        logger.error(f"Unexpected error: {e}")


def main():
    """Main function to run the bot."""
    logger.info("Starting Weather Bot...")

    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Error while running the bot: {e}")
    finally:
        logger.info("Weather Bot stopped.")


if __name__ == "__main__":
    main()
