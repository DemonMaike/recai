# Нужно написать асинхронную функцию для отправки сообщений логирования и файлов в телеграм через бота
# Данные бота recai_agent_bot token 7168820996:AAFxs6fH1ZbnVt16UjOJAKW8pu4l9SG7pYo
# Канал recai_info
import os
import aiohttp
from config import LOG_CHANNEL, BOT_TOKEN
import mimetypes


async def send_telegram_message(text, bot_token=BOT_TOKEN, chat_id=LOG_CHANNEL):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as response:
            return await response.json()  # Возвращает ответ от Telegram API


async def send_telegram_document(file_path, bot_token=BOT_TOKEN,
                                 chat_id=LOG_CHANNEL, caption=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    _, file_name = os.path.split(file_path)
    content_type, _ = mimetypes.guess_type(file_path)

    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('chat_id', chat_id)
        data.add_field('document', open(file_path, 'rb'),
                       filename=file_name,
                       content_type=content_type)
        if caption:
            data.add_field('caption', caption)

        async with session.post(url, data=data) as response:
            return await response.json()
