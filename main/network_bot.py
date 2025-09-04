import telebot
from telebot import types
import requests
import socket
import os
import logging
from dotenv import load_dotenv

# --- Настройки ---


load_dotenv()
TOKEN = os.getenv("NETWORK_BOT_TOKEN")  # Токен бота из .env файла
CONTENT_DIR = "content"  # Папка для хранения контента бота
BOT_PHOTO = "network_bot_photo.png"  # Имя файла с фото бота
REQUEST_TIMEOUT = 5  # Таймаут для HTTP-запросов в секундах
SOCKET_TIMEOUT = 1  # Таймаут для сокетов в секундах
DNS_IP = "8.8.8.8"  # Google Public DNS
DNS_PORT = 53  # DNS порт

if not TOKEN:
    raise ValueError(
        "Не установлена переменная окружения NETWORK_BOT_TOKEN. Создайте файл .env и добавьте в него NETWORK_BOT_TOKEN."
    )

bot = telebot.TeleBot(TOKEN)

# --- Функции-обработчики ---


def get_main_keyboard():
    """
    Создает основную клавиатуру бота

    Args:
        None

    Returns:
        types.ReplyKeyboardMarkup: Клавиатура с кнопками
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [types.KeyboardButton("🌐 Google"), types.KeyboardButton("🔍 DNS"), types.KeyboardButton("❓ Помощь")]
    markup.add(*buttons)
    return markup


@bot.message_handler(commands=["start"])
def start_command(message):
    """
    Приветствие пользователя и показ клавиатуры с командами.

    Args:
        message (telebot.types.Message): Сообщение от пользователя

    Returns:
        None
    """
    logging.info(f"Получено сообщение от {message.from_user.username}: {message.text}")

    markup = get_main_keyboard()

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        content_dir = os.path.join(script_dir, CONTENT_DIR)

        if not os.path.exists(content_dir):
            os.makedirs(content_dir)
            logging.warning(f"Создана папка {content_dir}")

        photo_path = os.path.join(content_dir, BOT_PHOTO)
        with open(photo_path, "rb") as file:
            bot.send_photo(message.chat.id, file)
    except FileNotFoundError:
        logging.warning(f"Фото не найдено по пути: {photo_path}")
    except Exception as e:
        logging.error(f"Ошибка при отправке фото: {e}")

    bot.send_message(
        message.chat.id,
        f"<b>Привет</b>, <em>{message.from_user.first_name}</em>, <b>тебя приветствует SocketSentryBot!</b>\n"
        "Я твой помощник для сетевой диагностики. Введи /help для списка команд.",
        parse_mode="html",
        reply_markup=markup,
    )


@bot.message_handler(commands=["check"])
def check_command(message):
    """
    Проверяет доступность указанного веб-сайта.

    Args:
        message (telebot.types.Message): Сообщение от пользователя, содержащее команду и URL сайта

    Returns:
        None
    """
    logging.info(f"Получено сообщение от {message.from_user.username}: {message.text}")

    markup = get_main_keyboard()
    response_message = ""

    try:
        url = message.text.split()[1]
        if not url.startswith("http"):
            url = "http://" + url

        bot.reply_to(message, f"Проверяю сайт {url}...")
        response = requests.get(url, timeout=REQUEST_TIMEOUT)

        if response.status_code == 200:
            response_message = f"✅ Сайт доступен. Статус: {response.status_code} OK"
        else:
            response_message = f"⚠️ Сайт ответил. Статус: {response.status_code}"

    except IndexError:
        response_message = "Пожалуйста, укажите адрес сайта после команды. Пример: /check google.com"
    except requests.ConnectionError:
        url_to_report = message.text.split()[1] if len(message.text.split()) > 1 else "указанный сайт"
        response_message = f"❌ Ошибка: Не удалось подключиться к сайту {url_to_report}."
    except Exception as e:
        response_message = f"Произошла непредвиденная ошибка: {e}"

    bot.send_message(message.chat.id, response_message, reply_markup=markup)


def check_port(ip, port):
    """
    Проверяет, открыт ли TCP-порт на указанном IP-адресе.

    Args:
        ip (str): IP-адрес для проверки
        port (int): Номер порта

    Returns:
        bool: True если порт открыт, False если закрыт"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(SOCKET_TIMEOUT)
        result = sock.connect_ex((ip, port))
        return result == 0  # Возвращает True, если порт открыт


@bot.message_handler(commands=["portscan"])
def portscan_command(message):
    """
    Проверяет открытые порты на указанном IP-адресе.

    Args:
        message (telebot.types.Message): Сообщение от пользователя, содержащее команду, IP и порт

    Returns:
        None
    """
    logging.info(f"Получено сообщение от {message.from_user.username}: {message.text}")

    markup = get_main_keyboard()
    response_message = ""

    try:
        parts = message.text.split()
        ip = parts[1]
        port = int(parts[2])

        bot.reply_to(message, f"Сканирую порт {port} на {ip}...")

        if check_port(ip, port):
            response_message = f"✅ Порт {port} на {ip} открыт."
        else:
            response_message = f"❌ Порт {port} на {ip} закрыт."

    except (IndexError, ValueError):
        response_message = "Пожалуйста, укажите IP-адрес и порт. Пример: /portscan 8.8.8.8 53"
    except Exception as e:
        response_message = f"Произошла ошибка: {e}"

    bot.send_message(message.chat.id, response_message, reply_markup=markup)


@bot.message_handler(commands=["help"])
def help_command(message):
    """
    Отправляет пользователю список доступных команд.

    Args:
        message (telebot.types.Message): Сообщение от пользователя, содержащее команду

    Returns:
        None
    """
    logging.info(f"Получено сообщение от {message.from_user.username}: {message.text}")

    message_info = f"""
<b>Доступные команды:</b>

/start - Начать общение с ботом
/help - Показать это сообщение
/check &lt;website&gt; - Проверить HTTP-статус сайта
/portscan &lt;ip-адрес&gt; &lt;порт&gt; - Проверить TCP-порт
    """
    bot.send_message(message.chat.id, message_info.strip(), parse_mode="html")


@bot.message_handler(content_types=["text"])
def handle_text(message):
    """
    Обрабатывает текстовые сообщения от пользователей.

    Args:
        message (telebot.types.Message): Сообщение от пользователя

    Returns:
        None
    """
    logging.info(f"Получено сообщение от {message.from_user.username}: {message.text}")

    if message.text == "🌐 Google":
        message.text = "/check google.com"
        check_command(message)
    elif message.text == "🔍 DNS":
        message.text = f"/portscan {DNS_IP} {DNS_PORT}"
        portscan_command(message)
    elif message.text == "❓ Помощь":
        help_command(message)
    else:
        bot.reply_to(message, "Неизвестная команда. Введите /help для списка доступных команд.")


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
