import telebot
from telebot import types
import requests
import socket
import os
import logging
import ipaddress
import re
from urllib.parse import urlparse
from dotenv import load_dotenv

# --- Settings ---

load_dotenv()
TOKEN = os.getenv("NETWORK_BOT_TOKEN")  # Bot token from .env file
CONTENT_DIR = "content"  # Directory for storing bot content
BOT_PHOTO = "network_bot_photo.png"  # Bot photo file name
REQUEST_TIMEOUT = 5  # HTTP request timeout in seconds
SOCKET_TIMEOUT = 1  # Socket timeout in seconds
DNS_IP = "8.8.8.8"  # Google Public DNS
DNS_PORT = 53  # DNS port

if not TOKEN:
    raise ValueError(
        "NETWORK_BOT_TOKEN environment variable is not set. Create a .env file and add NETWORK_BOT_TOKEN to it."
    )

bot = telebot.TeleBot(TOKEN)

# --- Validation Functions ---


def validate_ip(ip):
    """
    Validates IP address (IPv4 or IPv6).

    Args:
        ip (str): IP address to validate

    Returns:
        bool: True if IP is valid, False otherwise
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def validate_port(port):
    """
    Validates port number.

    Args:
        port (int): Port number to validate

    Returns:
        bool: True if port is valid, False otherwise
    """
    try:
        port_int = int(port)
        return 1 <= port_int <= 65535
    except (ValueError, TypeError):
        return False


def validate_url(url):
    """
    Validates URL format.

    Args:
        url (str): URL to validate

    Returns:
        bool: True if URL is valid, False otherwise
    """
    try:
        # Add protocol if missing
        if not url.startswith(("http://", "https://")):
            url = "http://" + url

        parsed = urlparse(url)
        # Check that domain exists and is not empty
        return bool(parsed.netloc) and "." in parsed.netloc
    except Exception:
        return False


def validate_domain(domain):
    """
    Validates domain name format.

    Args:
        domain (str): Domain name to validate

    Returns:
        bool: True if domain is valid, False otherwise
    """
    # Simple domain validation: contains dots, not empty, valid characters
    if not domain or len(domain) > 253:
        return False

    # Check that domain contains only valid characters
    domain_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
    return bool(re.match(domain_pattern, domain))


# --- Handler Functions ---


def get_main_keyboard():
    """
    Creates the main bot keyboard.

    Args:
        None

    Returns:
        types.ReplyKeyboardMarkup: Keyboard with buttons
    """
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [types.KeyboardButton("🌐 Google"), types.KeyboardButton("🔍 DNS"), types.KeyboardButton("❓ Help")]
    markup.add(*buttons)
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

    markup = get_main_keyboard()

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        content_dir = os.path.join(script_dir, CONTENT_DIR)

        if not os.path.exists(content_dir):
            os.makedirs(content_dir)
            logging.warning(f"Created directory {content_dir}")

        photo_path = os.path.join(content_dir, BOT_PHOTO)
        with open(photo_path, "rb") as file:
            bot.send_photo(message.chat.id, file)
    except FileNotFoundError:
        logging.warning(f"Photo not found at path: {photo_path}")
    except Exception as e:
        logging.error(f"Error sending photo: {e}")

    bot.send_message(
        message.chat.id,
        f"<b>Hello</b>, <em>{message.from_user.first_name}</em>, <b>welcome to SocketSentryBot!</b>\n"
        "I'm your network diagnostic assistant. Type /help for list of commands.",
        parse_mode="html",
        reply_markup=markup,
    )


@bot.message_handler(commands=["check"])
def check_command(message):
    """
    Checks availability of specified website.

    Args:
        message (telebot.types.Message): Message from user containing command and site URL

    Returns:
        None
    """
    logging.info(f"Received message from {message.from_user.username}: {message.text}")

    markup = get_main_keyboard()
    response_message = ""

    try:
        url = message.text.split()[1]

        # URL validation
        if not validate_url(url):
            response_message = "❌ Invalid URL format. Example: /check google.com"
            bot.send_message(message.chat.id, response_message, reply_markup=markup)
            return

        if not url.startswith("http"):
            url = "http://" + url

        bot.reply_to(message, f"Checking site {url}...")
        response = requests.get(url, timeout=REQUEST_TIMEOUT)

        if response.status_code == 200:
            response_message = f"✅ Site is available. Status: {response.status_code} OK"
        else:
            response_message = f"⚠️ Site responded. Status: {response.status_code}"

    except IndexError:
        response_message = "Please specify site address after command. Example: /check google.com"
    except requests.ConnectionError:
        url_to_report = message.text.split()[1] if len(message.text.split()) > 1 else "specified site"
        response_message = f"❌ Error: Could not connect to site {url_to_report}."
    except requests.Timeout:
        response_message = "⏰ Timeout: Site does not respond within 5 seconds."
    except Exception as e:
        response_message = f"An unexpected error occurred: {e}"

    bot.send_message(message.chat.id, response_message, reply_markup=markup)


def check_port(ip, port):
    """
    Checks if TCP port is open on specified IP address.

    Args:
        ip (str): IP address to check
        port (int): Port number

    Returns:
        bool: True if port is open, False if closed
    """
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(SOCKET_TIMEOUT)
        result = sock.connect_ex((ip, port))
        return result == 0  # Returns True if port is open
    except Exception as e:
        logging.error(f"Error checking port {port} on {ip}: {e}")
        return False
    finally:
        if sock:
            sock.close()


@bot.message_handler(commands=["portscan"])
def portscan_command(message):
    """
    Checks open ports on specified IP address.

    Args:
        message (telebot.types.Message): Message from user containing command, IP and port

    Returns:
        None
    """
    logging.info(f"Received message from {message.from_user.username}: {message.text}")

    markup = get_main_keyboard()
    response_message = ""

    try:
        parts = message.text.split()
        if len(parts) < 3:
            response_message = "Please specify IP address and port. Example: /portscan 8.8.8.8 53"
            bot.send_message(message.chat.id, response_message, reply_markup=markup)
            return

        ip = parts[1]
        port_str = parts[2]

        # IP address validation
        if not validate_ip(ip):
            response_message = f"❌ Invalid IP address: {ip}. Example: /portscan 8.8.8.8 53"
            bot.send_message(message.chat.id, response_message, reply_markup=markup)
            return

        # Port validation
        if not validate_port(port_str):
            response_message = f"❌ Invalid port number: {port_str}. Port must be between 1 and 65535."
            bot.send_message(message.chat.id, response_message, reply_markup=markup)
            return

        port = int(port_str)
        bot.reply_to(message, f"Scanning port {port} on {ip}...")

        if check_port(ip, port):
            response_message = f"✅ Port {port} on {ip} is open."
        else:
            response_message = f"❌ Port {port} on {ip} is closed."

    except (IndexError, ValueError) as e:
        response_message = f"❌ Parameter error: {e}. Example: /portscan 8.8.8.8 53"
    except Exception as e:
        response_message = f"An error occurred: {e}"

    bot.send_message(message.chat.id, response_message, reply_markup=markup)


@bot.message_handler(commands=["help"])
def help_command(message):
    """
    Sends user a list of available commands.

    Args:
        message (telebot.types.Message): Message from user containing command

    Returns:
        None
    """
    logging.info(f"Received message from {message.from_user.username}: {message.text}")

    message_info = f"""
<b>Available commands:</b>

/start - Start communication with bot
/help - Show this message
/check &lt;website&gt; - Check HTTP status of website
/portscan &lt;ip-address&gt; &lt;port&gt; - Check TCP port
    """
    bot.send_message(message.chat.id, message_info.strip(), parse_mode="html")


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

    if message.text == "🌐 Google":
        message.text = "/check google.com"
        check_command(message)
    elif message.text == "🔍 DNS":
        message.text = f"/portscan {DNS_IP} {DNS_PORT}"
        portscan_command(message)
    elif message.text == "❓ Help":
        help_command(message)
    else:
        bot.reply_to(message, "Unknown command. Type /help for list of available commands.")


# --- Main Launch Logic ---


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logging.info("Network diagnostic bot started...")
    try:
        bot.infinity_polling()
    except Exception as e:
        logging.error(f"Bot stopped due to error: {e}")
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
    finally:
        logging.info("Bot stopped.")
