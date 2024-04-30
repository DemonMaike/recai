import os

from dotenv import load_dotenv


load_dotenv()
# database
DB_NAME = os.getenv("DATABASE_NAME")
DB_USER = os.getenv("DATABASE_USER")
DB_PASS = os.getenv("DATABASE_PASS")
DB_PORT = os.getenv("DATABASE_PORT")
DB_HOST = os.getenv("DATABASE_HOST")

# Auth
JWT_SECRET = os.getenv("JWT_SECRET")
RESET_PASS_SECRET = os.getenv("RESET_PASS_SECRET")

# rabbitmq
RABBIT_HOST = os.getenv("RABBIT_HOST")
RABBIT_ADMIN = os.getenv("RABBIT_ADMIN")
RABBIT_ADMIN_PASS = os.getenv("RABBIT_ADMIN_PASS")
RABBIT_QUEUE_PORT = os.getenv("RABBIT_QUEUE_PORT")
RABBIT_MANAGMENT_PORT = os.getenv("RABBIT_MANAGMENT_PORT")

# whisper env

# llm env


# Telegram channel
BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_CHANNEL = os.getenv("LOG_CHANNEL")
