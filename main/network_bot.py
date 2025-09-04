from email.mime import message
import telebot
from telebot import types
import requests
import socket
import os
import logging
from dotenv import load_dotenv

# --- Настройки ---
load_dotenv()

TOKEN = os.getenv("NETWORK_BOT_TOKEN")
if not TOKEN:
    raise ValueError(
        "Не установлена переменная окружения NETWORK_BOT_TOKEN. Создайте файл .env и добавьте в него NETWORK_BOT_TOKEN."
    )

bot = telebot.TeleBot(TOKEN)

# --- Функции-обработчики ---


@bot.message_handler(commands=["start"])
def start_command(message):
    markup = types.ReplyKeyboardMarkup()
    btn1 = types.KeyboardButton("/check google.com")
    btn2 = types.KeyboardButton("/portscan 8.8.8.8 53")
    markup.row(btn1, btn2)

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        photo_path = os.path.join(script_dir, "content", "network_bot_photo.png")
        with open(photo_path, "rb") as file:
            bot.send_photo(message.chat.id, file)
    except FileNotFoundError:
        logging.warning("Фото для команды /start не найдено.")

    bot.send_message(
        message.chat.id,
        f"<b>Привет</b>, <em>{message.from_user.first_name}</em>, <b>тебя приветствует SocketSentryBot!</b>\n"
        "Я твой помощник для сетевой диагностики. Введи /help для списка команд.",
        parse_mode="html",
        reply_markup=markup,
    )


@bot.message_handler(commands=["check"])
def check_command(message):
    try:
        url = message.text.split()[1]

        if not url.startswith("http"):
            url = "http://" + url

        bot.reply_to(message, f"Проверяю сайт {url}...")
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            bot.send_message(message.chat.id, f"✅ Сайт доступен. Статус: {response.status_code} OK")
        else:
            bot.send_message(message.chat.id, f"⚠️ Сайт ответил. Статус: {response.status_code}")

    except IndexError:
        bot.reply_to(message, "Пожалуйста, укажите адрес сайта после команды. Пример: /check google.com")
    except requests.ConnectionError:
        url_to_report = message.text.split()[1] if len(message.text.split()) > 1 else "указанный сайт"
        bot.send_message(message.chat.id, f"Ошибка: Не удалось подключиться к сайту {url_to_report}.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла непредвиденная ошибка: {e}")


def check_port(ip, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))
        return result == 0


@bot.message_handler(commands=["portscan"])
def portscan_command(message):
    try:
        parts = message.text.split()
        ip = parts[1]
        port = int(parts[2])

        bot.reply_to(message, f"Сканирую порт {port} на {ip}...")

        if check_port(ip, port):
            bot.send_message(message.chat.id, f"✅ Порт {port} на {ip} открыт.")
        else:
            bot.send_message(message.chat.id, f"❌ Порт {port} на {ip} закрыт.")

    except (IndexError, ValueError):
        bot.reply_to(message, "Пожалуйста, укажите IP-адрес и порт. Пример: /portscan 8.8.8.8 53")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}")


@bot.message_handler(commands=["help"])
def help_command(message):
    message_info = f"""
<b>Доступные команды:</b>

/start - Начать общение с ботом
/help - Показать это сообщение
/check &lt;website&gt; - Проверить HTTP-статус сайта
/portscan &lt;ip-адрес&gt; &lt;порт&gt; - Проверить TCP-порт
    """
    bot.send_message(message.chat.id, message_info.strip(), parse_mode="html")


# --- Основная логика запуска ---


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Бот для работы с сетями запущен...")
    try:
        bot.infinity_polling()
    except Exception as e:
        logging.error(f"Бот остановлен из-за ошибки: {e}")
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем.")
    finally:
        logging.info("Бот остановлен.")
