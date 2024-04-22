import os

from dotenv import load_dotenv


load_dotenv()
# database env
DB_NAME = os.getenv("DATABASE_NAME")
DB_USER = os.getenv("DATABASE_USER")
DB_PASS = os.getenv("DATABASE_PASS")
DB_PORT = os.getenv("DATABASE_PORT")
DB_HOST = os.getenv("DATABASE_HOST")

# Auth
JWT_SECRET = os.getenv("JWT_SECRET")

# rabbitmq env

# whisper env

# llm env
