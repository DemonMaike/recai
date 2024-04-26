import asyncio
import json
import aiohttp  # Для отправки HTTP запросов в асинхронном режиме
import mimetypes
import aiofiles

from aio_pika import connect, IncomingMessage
from aio_pika.exceptions import QueueEmpty, MessageProcessError
from config import RABBIT_ADMIN, RABBIT_ADMIN_PASS, RABBIT_HOST, RABBIT_QUEUE_PORT


# дальше для обработки по 2-3 сообщения можем добавить семафоры.
async def main():
    connection = await connect(f"amqp://{RABBIT_ADMIN}:{RABBIT_ADMIN_PASS}@{RABBIT_HOST}:{RABBIT_QUEUE_PORT}/")
    channel = await connection.channel()  # Создаем канал связи

    diarize_queue = await channel.declare_queue('DiarizationQueue', durable=True)
    semaphore = asyncio.Semaphore(1)
    url = "localhost:5000/transcribe"

    async def process_message(message: IncomingMessage):
        async with semaphore:
            async with message.process():
                data = json.loads(message.body.decode())
                try:
                    file_path = data['file_path']
                    file_name = file_path.split("/")[-1]
                    out_file_path = f"static/text/{file_name.rstrip('.').txt}"
                    mime = mimetypes.guess_type(file_name)

                    # Отправляем данные в контейнер и ждем ответа
                    async with aiohttp.ClientSession() as session:
                        try:
                            with open(file_path, 'rb') as file:
                                data = aiohttp.FormData()
                                data.add_field('audio',
                                               file,
                                               filename=file_name,
                                               content_type=mime)

                            response = await session.post(url, data=data)
                            response_json = await response.json()

                            # сохранить файл, асинхронно
                            async with aiofiles.open(out_file_path, "w") as f:
                                for segment in response_json["segments"]:
                                    speaker = segment.get(
                                        "speaker", "Unknown Speaker")
                                    start_time = segment["start"]
                                    finish_time = segment["end"]
                                    text = segment["text"].strip()
                                    # Формируем строку для каждого сегмента и записываем её в файл
                                    await f.write(f"{speaker}\n{start_time}...{finish_time}\n{text}\n\n")

                            await message.ack()
                        except Exception as e:
                            print("Ошибка при отправке запроса:", e)
                            await message.nack(requeue=True)

                # Получение следующего сообщения вручную
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
