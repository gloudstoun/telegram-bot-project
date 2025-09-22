import telebot
from telebot import types
import sqlite3
import hashlib
import os
import logging
from dotenv import load_dotenv

# --- Settings ---
load_dotenv()

TOKEN = os.getenv("DATABASE_BOT_TOKEN")  # Bot token from .env file
MIN_PASSWORD_LENGTH = 8  # Minimum password length
BOT_PHOTO = "database_bot_photo.png"  # Bot photo file name

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Script directory
CONTENT_DIR = os.path.join(SCRIPT_DIR, "content")  # Content directory
DB_FILE = os.path.join(SCRIPT_DIR, "users_list.db")  # Database file

if not TOKEN:
    raise ValueError(
        "DATABASE_BOT_TOKEN environment variable is not set. Create a .env file and add DATABASE_BOT_TOKEN to it."
    )

bot = telebot.TeleBot(TOKEN)


# --- Database Management ---


def init_db():
    """
    Initializes the database and creates the table if it doesn't exist.

    Args:
        None

    Returns:
        None
    """
    conn = None
    cur = None
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
        logging.info("Database successfully initialized")
    except sqlite3.Error as e:
        logging.error(f"Error initializing database: {e}")
        raise
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def hash_password(password):
    """
    Hashes password using SHA-256.

    Args:
        password (str): Password to hash

    Returns:
        str: Hashed password
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def add_user(name, password):
    """
    Adds a new user to the database if the name is not taken.

    Args:
        name (str): Username
        password (str): User password

    Returns:
        bool: True if user successfully added, False if name already taken
    """
    conn = None
    cur = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        pass_hash = hash_password(password)
        cur.execute("INSERT INTO users (name, pass_hash) VALUES (?, ?)", (name, pass_hash))
        conn.commit()
    except sqlite3.IntegrityError:
        logging.warning("Name already taken")
        return False  # Name already taken
    except sqlite3.Error as e:
        logging.error(f"Error adding user: {e}")
        return False  # Error adding user
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return True  # User successfully added


def is_name_taken(name):
    """
    Checks if username is taken in the database.

    Args:
        name (str): Username to check

    Returns:
        bool: True if name is taken, otherwise False
    """
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE name = ?", (name,))
        is_taken = cur.fetchone() is not None
        return is_taken
    except sqlite3.Error as e:
        logging.error(f"Error checking name availability: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def get_all_users():
    """
    Gets list of all users from the database.

    Args:
        None

    Returns:
        list of tuples: List of users in format (id, name)
    """
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return users


# --- Telegram Command Handlers ---


def get_main_keyboard():
    """
    Creates the main bot keyboard.

    Args:
        None

    Returns:
        telebot.types.ReplyKeyboardMarkup: Keyboard with main commands
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        types.KeyboardButton("👤 Registration"),
        types.KeyboardButton("📋 User List"),
        types.KeyboardButton("❓ Help"),
    ]
    markup.add(*buttons)
    return markup


def get_back_keyboard():
    """
    Creates keyboard with "Back" button.

    Args:
        None

    Returns:
        telebot.types.ReplyKeyboardMarkup: Keyboard with "Back" button
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    back_button = types.KeyboardButton("🔙 Back")
    markup.add(back_button)
    return markup


@bot.message_handler(commands=["start"])
def start_command(message):
    """
    Greets the user and shows keyboard with commands.

    Args:
        message (telebot.types.Message): Message from user

    Returns:
        None
    """
    logging.info(f"Received message from {message.from_user.username}: {message.text}")
    markup_main = get_main_keyboard()

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        photo_path = os.path.join(script_dir, CONTENT_DIR, BOT_PHOTO)
        with open(photo_path, "rb") as file:
            bot.send_photo(message.chat.id, file)
    except FileNotFoundError:
        logging.warning("Photo for /start command not found.")

    bot.send_message(
        message.chat.id,
        f"<b>Hello</b>, <em>{message.from_user.first_name}</em>, <b>welcome to SimpleRegistryBot!</b>\n"
        f"This bot allows you to register users and store them in an SQLite database.\n"
        f"Use the buttons below or enter a command to start working.",
        parse_mode="html",
        reply_markup=markup_main,
    )


def is_valid_name(name):
    """
    Checks that name contains only letters and is not empty.

    Args:
        name (str): Name to check

    Returns:
        bool: True if name is valid, otherwise False
    """
    return bool(name) and name.isalpha()


def process_name_step(message):
    """
    Processes username input.

    Args:
        message (telebot.types.Message): Message from user with name

    Returns:
        None
    """
    response_message = ""
    markup_back = get_back_keyboard()
    markup_main = get_main_keyboard()

    logging.info(f"Received message from {message.from_user.username}: {message.text}")

    if message.text == "🔙 Back" or message.text == "/back":
        bot.send_message(
            message.chat.id,
            "You returned to the main menu. Enter /help for list of available commands.",
            reply_markup=markup_main,
        )
        return

    username = message.text.strip()
    if is_name_taken(username):
        bot.send_message(
            message.chat.id,
            "This name is already taken. Try another one: ",
            reply_markup=markup_back,
        )
        bot.register_next_step_handler(message, process_name_step)
        return

    if not is_valid_name(username):
        bot.send_message(
            message.chat.id,
            "Name cannot be empty and must contain only letters. Try again:",
            reply_markup=markup_back,
        )
        bot.register_next_step_handler(message, process_name_step)
        return

    response_message = "Great! Now enter a password (minimum 8 characters, letters and numbers):"

    bot.send_message(message.chat.id, response_message, reply_markup=markup_back)
    bot.register_next_step_handler(message, process_password_step, username)


def is_strong_password(password):
    """
    Checks password strength: minimum 8 characters, letters and numbers.

    Args:
        password (str): Password to check

    Returns:
        bool: True if password is strong, otherwise False
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        return False
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_letter and has_digit


def process_password_step(message, username):
    """
    Processes password and completes registration.

    Args:
        message (telebot.types.Message): Message from user with password
        username (str): Username entered earlier

    Returns:
        None
    """
    response_message = ""
    markup_back = get_back_keyboard()
    markup_main = get_main_keyboard()

    logging.info(f"Received message from {message.from_user.username}: {message.text}")

    if message.text == "🔙 Back" or message.text == "/back":
        bot.send_message(
            message.chat.id,
            "You returned to the main menu. Enter /help for list of available commands.",
            reply_markup=markup_main,
        )
        return

    password = message.text.strip()
    if not is_strong_password(password):
        bot.send_message(
            message.chat.id,
            "Password must be at least 8 characters and contain letters and numbers. Try again:",
            reply_markup=markup_back,
        )
        bot.register_next_step_handler(message, process_password_step, username)
        return

    if add_user(username, password):
        response_message = f"User <b>{username}</b> successfully registered!"
    else:
        response_message = "Registration error. Please try again."

    bot.send_message(message.chat.id, response_message, reply_markup=markup_main, parse_mode="HTML")


def help_command(message):
    """
    Sends user a list of available commands.

    Args:
        message (telebot.types.Message): Message from user containing command

    Returns:
        None
    """
    markup_main = get_main_keyboard()
    logging.info(f"Received message from {message.from_user.username}: {message.text}")

    message_info = f"""<b>Available commands:</b>
    /help - Show this message
    /start - Restart bot and show main menu
    /registration - Start new user registration process
    /list - Show list of all registered users
    """

    bot.send_message(message.chat.id, message_info, parse_mode="HTML", reply_markup=markup_main)


@bot.message_handler(content_types=["text"])
def handle_text(message):
    """
    Handles text messages from users.

    Args:
        message (telebot.types.Message): Message from user

    Returns:
        None
    """
    logging.info(f"Received message from {message.from_user.username}: {message.text}")
    markup_main = get_main_keyboard()
    markup_back = get_back_keyboard()

    if message.text == "👤 Registration" or message.text == "/registration":
        bot.send_message(message.chat.id, "Please enter your name (letters only):", reply_markup=markup_back)
        bot.register_next_step_handler(message, process_name_step)
    elif message.text == "📋 User List" or message.text == "/list":
        users = get_all_users()
        if not users:
            info = "No users in database yet."
        else:
            info = "Registered users:\n\n"
            for user_id, name in users:
                info += f"ID: {user_id}, Name: {name}\n"
        bot.send_message(message.chat.id, info, reply_markup=markup_main)
    elif message.text == "❓ Help" or message.text == "/help":
        help_command(message)
    else:
        bot.reply_to(message, "Unknown command. Enter /help for list of available commands.", reply_markup=markup_main)


# --- Main Launch Logic ---


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    init_db()
    logging.info("Database bot started...")
    try:
        bot.infinity_polling()
    except Exception as e:
        logging.error(f"Bot stopped due to error: {e}")
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
    finally:
        logging.info("Bot stopped.")
