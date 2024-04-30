# Нужно написать асинхронную функцию для отправки сообщений логирования и файлов в телеграм через бота
# Данные бота recai_agent_bot token 7168820996:AAFxs6fH1ZbnVt16UjOJAKW8pu4l9SG7pYo
# Канал recai_info
import os
import requests
import mimetypes

from config import BOT_TOKEN, LOG_CHANNEL


def send_telegram_message(text, bot_token=BOT_TOKEN, chat_id=LOG_CHANNEL):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(url, data=data)
    return response.json()


def send_telegram_document(file_path, bot_token=BOT_TOKEN, chat_id=LOG_CHANNEL, caption=None):
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    _, file_name = os.path.split(file_path)
    content_type, _ = mimetypes.guess_type(file_path)
    with open(file_path, 'rb') as file:
        files = {
            'document': (file_name, file, content_type)
        }
        data = {'chat_id': chat_id}
        if caption:
            data['caption'] = caption
        response = requests.post(url, data=data, files=files)
    return response.json()
