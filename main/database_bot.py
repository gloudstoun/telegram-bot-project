import telebot
from telebot import types
import sqlite3
import hashlib
import os
import logging

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")
DB_FILE = "users_list.db"  # Используем расширение .db для баз данных SQLite
bot = telebot.TeleBot(TOKEN)
bot = telebot.TeleBot(TOKEN)

# --- Управление базой данных ---


def init_db():
    """
    Инициализирует базу данных и создает таблицу, если ее нет.
    Эту функцию нужно вызвать один раз при старте бота.
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # Оптимизированный и корректный SQL-запрос для SQLite
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        pass_hash TEXT NOT NULL
    )
    """
    )
    conn.commit()
    cur.close()
    conn.close()


def hash_password(password):
    """Хэширует пароль с помощью SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def add_user(name, password):
    """Добавляет нового пользователя в базу данных, если имя не занято."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    # Проверяем, существует ли пользователь с таким именем
    cur.execute("SELECT id FROM users WHERE name = ?", (name,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return False  # Имя занято
    pass_hash = hash_password(password)
    cur.execute("INSERT INTO users (name, pass_hash) VALUES (?, ?)", (name, pass_hash))
    conn.commit()
    cur.close()
    conn.close()
    return True  # Успешно добавлен

def get_all_users():
    """Получает список всех пользователей из базы данных."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM users")  # Не выбираем пароли для отображения
    users = cur.fetchall()
    cur.close()
    conn.close()
    return users


# --- Обработчики команд Telegram ---


@bot.message_handler(commands=["start"])
def start_command(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Показать список пользователей", callback_data="show_users"))
    markup.add(types.InlineKeyboardButton("Регистрация нового пользователя", callback_data="registration"))

    photo_path = os.path.join("content", "database_bot_photo.png")
    with open(photo_path, "rb") as file:
        bot.send_photo(message.chat.id, file)

    bot.send_message(
        message.chat.id,
        f"<b>Привет</b>, <em>{message.from_user.first_name}</em>, <b>тебя приветствует SimpleRegistryBot!</b>\n"
        "Проверь список пользователей и пополни его!",
        parse_mode="html",
        reply_markup=markup,
    )


@bot.message_handler(commands=["registration"])
def registration_command(message):
    bot.send_message(message.chat.id, "Введите ваше имя для регистрации:")
    # Переходим к следующему шагу - получению имени
    bot.register_next_step_handler(message, process_name_step)


def process_name_step(message):
def is_strong_password(password):
    """Проверяет надежность пароля: минимум 8 символов, буквы и цифры."""
    if len(password) < 8:
        return False
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_letter and has_digit

def process_password_step(message, username):
    """Обрабатывает пароль и завершает регистрацию."""
    password = message.text.strip()
    if not is_strong_password(password):
        bot.send_message(
            message.chat.id,
            "Пароль должен быть не менее 8 символов и содержать буквы и цифры. Попробуйте снова:"
        )
        bot.register_next_step_handler(message, process_password_step, username)
        return

    add_user(username, password)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Показать список пользователей", callback_data="show_users"))
    bot.send_message(message.chat.id, "Вы успешно зарегистрированы!", reply_markup=markup)
    """Обрабатывает пароль и завершает регистрацию."""
    password = message.text.strip()
    add_user(username, password)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Показать список пользователей", callback_data="show_users"))
    bot.send_message(message.chat.id, "Вы успешно зарегистрированы!", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "show_users")
def show_users_callback(call):
    """Обрабатывает нажатие на кнопку 'Показать список пользователей'."""
    users = get_all_users()

    if not users:
        info = "В базе данных пока нет пользователей."
    else:
        info = "Зарегистрированные пользователи:\n\n"
        for user_id, name in users:
if __name__ == "__main__":
    # Убеждаемся, что таблица в базе данных существует перед запуском
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    init_db()
    logging.info("Бот для работы с БД запущен...")
    bot.infinity_polling()

@bot.callback_query_handler(func=lambda call: call.data == "registration")
def registration_callback(call):
    """Обрабатывает нажатие на кнопку 'Регистрация нового пользователя'."""
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Введите ваше имя для регистрации:")
    bot.register_next_step_handler(call.message, process_name_step)
    bot.send_message(call.message.chat.id, info)


# --- Основной запуск ---
if __name__ == "__main__":
    # Убеждаемся, что таблица в базе данных существует перед запуском
    init_db()
    print("Бот для работы с БД запущен...")
    bot.infinity_polling()
