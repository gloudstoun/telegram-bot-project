import telebot
from telebot import types
import sqlite3
import hashlib
import os
import logging
from dotenv import load_dotenv

# --- Настройки ---
load_dotenv()

TOKEN = os.getenv("DATABASE_BOT_TOKEN")  # Токен бота из .env файла
CONTENT_DIR = "content"  # Папка для хранения контента бота
BOT_PHOTO = "database_bot_photo.png"  # Имя файла с фото бота
MIN_PASSWORD_LENGTH = 8  # Минимальная длина пароля
DB_FILE = "users_list.db"  # Файл базы данных

if not TOKEN:
    raise ValueError(
        "Не установлена переменная окружения DATABASE_BOT_TOKEN. Создайте файл .env и добавьте в него DATABASE_BOT_TOKEN."
    )

bot = telebot.TeleBot(TOKEN)


# --- Управление базой данных ---


def init_db():
    """
    Инициализирует базу данных и создает таблицу, если ее нет.

    Args:
        None

    Returns:
        None
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                pass_hash TEXT NOT NULL
            )
        """
        )
        conn.commit()
        logging.info("База данных успешно инициализирована")
    except sqlite3.Error as e:
        logging.error(f"Ошибка при инициализации БД: {e}")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def hash_password(password):
    """
    Хэширует пароль с помощью SHA-256.

    Args:
        password (str): Пароль для хэширования

    Returns:
        str: Хэшированный пароль
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def add_user(name, password):
    """
    Добавляет нового пользователя в базу данных, если имя не занято.

    Args:
        name (str): Имя пользователя
        password (str): Пароль пользователя

    Returns:
        bool: True если пользователь успешно добавлен, False если имя уже занято
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()

        pass_hash = hash_password(password)
        cur.execute("INSERT INTO users (name, pass_hash) VALUES (?, ?)", (name, pass_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        logging.warning("Имя уже занято")
        return False  # Имя уже занято
    except sqlite3.Error as e:
        logging.error(f"Ошибка при добавлении пользователя: {e}")
        return False  # Ошибка при добавлении пользователя
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return True  # Пользователь успешно добавлен


def is_name_taken(name):
    """
    Проверяет, занято ли имя пользователя в базе данных.

    Args:
        name (str): Имя пользователя для проверки

    Returns:
        bool: True если имя занято, иначе False
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE name = ?", (name,))
        is_taken = cur.fetchone() is not None
        return is_taken
    except sqlite3.Error as e:
        logging.error(f"Ошибка при проверке занятости имени: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def get_all_users():
    """
    Получает список всех пользователей из базы данных.

    Args:
        None

    Returns:
        list of tuples: Список пользователей в формате (id, name)
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return users


# --- Обработчики команд Telegram ---


def get_main_keyboard():
    """
    Создает основную клавиатуру бота.

    Args:
        None

    Returns:
        telebot.types.ReplyKeyboardMarkup: Клавиатура с основными командами
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("👤 Регистрация"),
        types.KeyboardButton("📋 Список пользователей"),
        types.KeyboardButton("❓ Помощь"),
    ]
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
        photo_path = os.path.join(script_dir, CONTENT_DIR, BOT_PHOTO)
        with open(photo_path, "rb") as file:
            bot.send_photo(message.chat.id, file)
    except FileNotFoundError:
        logging.warning("Фото для команды /start не найдено.")

    bot.send_message(
        message.chat.id,
        f"<b>Привет</b>, <em>{message.from_user.first_name}</em>, <b>тебя приветствует SimpleRegistryBot!</b>\n"
        f"Этот бот позволяет регистрировать пользователей и хранить их в базе данных SQLite.\n"
        f"Используй кнопки ниже или введи команду для начала работы.",
        parse_mode="html",
        reply_markup=markup,
    )


def is_valid_name(name):
    """
    Проверяет, что имя состоит только из букв и не пустое.

    Args:
        name (str): Имя для проверки

    Returns:
        bool: True если имя валидно, иначе False
    """
    return bool(name) and name.isalpha()


def process_name_step(message):
    """
    Обрабатывает ввод имени пользователя.

    Args:
        message (telebot.types.Message): Сообщение от пользователя с именем

    Returns:
        None
    """
    markup = get_main_keyboard()
    logging.info(f"Получено сообщение от {message.from_user.username}: {message.text}")
    response_message = ""
    username = message.text.strip()

    if is_name_taken(username):
        bot.send_message(
            message.chat.id,
            "Это имя уже занято. Пожалуйста, начните регистрацию заново с другим именем: /registration",
            reply_markup=markup,
        )
        return

    if not is_valid_name(username):
        bot.send_message(message.chat.id, "Имя не может быть пустым и должно содержать только буквы. Попробуйте снова:")
        bot.register_next_step_handler(message, process_name_step)
        return

    response_message = "Отлично! Теперь введите пароль (минимум 8 символов, буквы и цифры):"

    bot.send_message(message.chat.id, response_message)
    bot.register_next_step_handler(message, process_password_step, username)


def is_strong_password(password):
    """
    Проверяет надежность пароля: минимум 8 символов, буквы и цифры.

    Args:
        password (str): Пароль для проверки

    Returns:
        bool: True если пароль надежный, иначе False
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_letter and has_digit


def process_password_step(message, username):
    """
    Обрабатывает пароль и завершает регистрацию.

    Args:
        message (telebot.types.Message): Сообщение от пользователя с паролем
        username (str): Имя пользователя, введенное ранее

    Returns:
        None
    """
    response_message = ""
    markup = get_main_keyboard()

    password = message.text.strip()
    if not is_strong_password(password):
        bot.send_message(
            message.chat.id, "Пароль должен быть не менее 8 символов и содержать буквы и цифры. Попробуйте снова:"
        )
        bot.register_next_step_handler(message, process_password_step, username)
        return

    if add_user(username, password):
        response_message = f"Пользователь <b>{username}</b> успешно зарегистрирован!"
    else:
        response_message = "Ошибка при регистрации. Попробуйте снова."

    bot.send_message(message.chat.id, response_message, reply_markup=markup, parse_mode="HTML")


def help_command(message):
    """
    Отправляет пользователю список доступных команд.

    Args:
        message (telebot.types.Message): Сообщение от пользователя, содержащее команду

    Returns:
        None
    """
    markup = get_main_keyboard()
    logging.info(f"Получено сообщение от {message.from_user.username}: {message.text}")

    message_info = f"""<b>Доступные команды:</b>
    /help - Показать это сообщение
    /start - Перезапустить бота и показать главное меню
    /registration - Начать процесс регистрации нового пользователя
    /list - Показать список всех зарегистрированных пользователей
    """

    bot.send_message(message.chat.id, message_info, parse_mode="HTML", reply_markup=markup)


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
    markup = get_main_keyboard()

    if message.text == "👤 Регистрация" or message.text == "/registration":
        bot.send_message(message.chat.id, "Пожалуйста, введите ваше имя (только буквы):", reply_markup=markup)
        bot.register_next_step_handler(message, process_name_step)

    elif message.text == "📋 Список пользователей" or message.text == "/list":
        users = get_all_users()
        if not users:
            info = "В базе данных пока нет пользователей."
        else:
            info = "Зарегистрированные пользователи:\n\n"
            for user_id, name in users:
                info += f"ID: {user_id}, Имя: {name}\n"
        bot.send_message(message.chat.id, info, reply_markup=markup)

    elif message.text == "❓ Помощь" or message.text == "/help":
        help_command(message)

    else:
        bot.reply_to(message, "Неизвестная команда. Введите /help для списка доступных команд.", reply_markup=markup)


# --- Основная логика запуска ---


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    init_db()
    logging.info("Бот для работы с БД запущен...")
    try:
        bot.infinity_polling()
    except Exception as e:
        logging.error(f"Бот остановлен из-за ошибки: {e}")
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем.")
    finally:
        logging.info("Бот остановлен.")
