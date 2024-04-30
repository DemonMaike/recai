# Нужно сделать прослушивание очереди AnswerQueue
# Получить статус задачи
# Просто передаем путь к файлу, логика предусматривает аткуализацию данного параметра на ранних стадиях до того как сообщение попадет сюда.
# Отправка
# Актуализация статуса в базе, указываем что задача завершена.

import asyncio
import json

from aio_pika import connect
from aio_pika import IncomingMessage
from config import RABBIT_ADMIN, RABBIT_ADMIN_PASS, RABBIT_HOST, RABBIT_QUEUE_PORT
from senders.tg import send_telegram_document


async def main():
    connection = await connect(f"amqp://{RABBIT_ADMIN}:{RABBIT_ADMIN_PASS}@{RABBIT_HOST}:{RABBIT_QUEUE_PORT}/")
    channel = await connection.channel()  # Создаем канал связи

    main_queue = await channel.declare_queue('AnswerQueue', durable=True)

    async def on_message(message: IncomingMessage):
        async with message.process():
            data = json.loads(message.body.decode())
            print(data)

            if "file_path" in data and data["file_path"] is not None:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, send_telegram_document, data['file_path'])
                print(
                    f"информация о задаче {data['task_id']} направлена в telegram")
            else:
                print("Проблема с file_path")

            # Изменить в бд статус.

    await main_queue.consume(on_message)
    print("Агент ответов запущен и слушает очередь 'AnswerQueue'.")

    await asyncio.Future()  # Запускаем бесконечный цикл

if __name__ == '__main__':
    asyncio.run(main())
