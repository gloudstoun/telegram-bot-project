import telebot
from telebot import types
import sqlite3
import hashlib
import os
import logging
from dotenv import load_dotenv

# --- Настройки ---
load_dotenv()

TOKEN = os.getenv("WEATHER_BOT_TOKEN")  # Токен бота из .env файла

BOT_PHOTO = "weather_bot_photo.png"  # Имя файла с фото бота

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # Директория скрипта
CONTENT_DIR = os.path.join(SCRIPT_DIR, "content")  # Директория с контентом
DB_FILE = os.path.join(SCRIPT_DIR, "users_list.db")  # Файл базы данных

if not TOKEN:
    raise ValueError(
        "Не установлена переменная окружения DATABASE_BOT_TOKEN. Создайте файл .env и добавьте в него DATABASE_BOT_TOKEN."
    )

bot = telebot.TeleBot(TOKEN)
