import asyncio
import json
import aiohttp  # Для отправки HTTP запросов в асинхронном режиме

from aio_pika import connect, IncomingMessage
from aio_pika.exceptions import QueueEmpty, MessageProcessError
from config import RABBIT_ADMIN, RABBIT_ADMIN_PASS, RABBIT_HOST, RABBIT_QUEUE_PORT


# дальше для обработки по 2-3 сообщения можем добавить семафоры.
async def main():
    connection = await connect(f"amqp://{RABBIT_ADMIN}:{RABBIT_ADMIN_PASS}@{RABBIT_HOST}:{RABBIT_QUEUE_PORT}/")
    channel = await connection.channel()  # Создаем канал связи

    diarize_queue = await channel.declare_queue('DiarizationQueue', durable=True)
    semaphore = asyncio.Semaphore(1)
    message_lock = asyncio.Lock()

    async def process_message(message: IncomingMessage):
        async with semaphore:
            async with message_lock:
                async with message.process():
                    data = json.loads(message.body.decode())
                    try:
                        file_path = data['file_path']
                        print(file_path)
                    # Отправляем данные в контейнер и ждем ответа
                    # async with aiohttp.ClientSession() as session:
                    #     try:
                    #         response = await session.post('http://localhost:5000/transcribe', json=data)
                    #         response_data = await response.json()
                    #         # сохранить файл, асинхронно
                    #         print("Получен ответ:", response_data)
                    #         await message.ack()
                    #     except Exception as e:
                    #         print("Ошибка при отправке запроса:", e)
                    #         await message.nack(requeue=True)
                    # # Получение следующего сообщения вручную
                    except Exception as e:
                        print(f"Ошибка {e}")

    async def consume_messages():
        while True:
            try:
                message = await diarize_queue.get(no_ack=False)
                asyncio.create_task(process_message(message))
            except QueueEmpty:
                pass
            except MessageProcessError:
                pass

    print("Агент диаризацции запущен и слушает очередь 'DiarizationQueue'.")
    await consume_messages()  # Начинаем обработку первого сообщения

if __name__ == '__main__':
    asyncio.run(main())
