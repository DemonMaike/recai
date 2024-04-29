import os
import asyncio
import json

from docx import Document
import aiohttp
import pika
import aiofiles


UPLOAD_FOLDER = "static/report"


def create_docx(filename: str, text: str) -> None:
    out_path = os.path.join(UPLOAD_FOLDER, filename)
    doc = Document()
    doc.add_paragrah(text)
    doc.save(out_path)
    print(out_path, " created")


async def handle_task(session, file_path):
    loop = asyncio.get_event_loop()
    file_name = os.path.split(file_path)[-1]
    # нужно определять mime-type через mimetypes
    base_name, ext = os.path.splitext(file_name)
    out_name = base_name + ".docx"

    data = aiohttp.FormData()
    data.add_field(
        'file',
        open(file_path, 'rb'),
        filename=file_name,
        content_type=f"text/plain")

    try:
        # Отправляем задачу в контейнер, в дальнейшем должен быть хаб.
        async with session.post('http://127.0.0.1:5001/create_report',
                                data=data, timeout=500) as response:
            if response.status == 200:
                result = await response.json()

                await loop.run_in_executor(None, create_docx, out_name, result)
                print("Файл создан")

            else:
                print("Ошибка при обработке запроса.")
    except aiohttp.ClientError as e:
        print("Ошибка соединения: ", e)


async def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        'localhost', 5672, '/', pika.PlainCredentials("admin", "admin")))
    channel = connection.channel()
    channel.queue_declare(queue='LLMQueue', durable=True)

    async with aiohttp.ClientSession() as session:
        while True:
            method_frame, properties, body = next(channel.consume(
                'LLMQueue', inactivity_timeout=None))
            if method_frame:
                print("Recived message. Working...")
                body_decoded = body.decode("utf-8")
                body_data = json.loads(body_decoded)

                task = asyncio.create_task(
                    handle_task(session, body_data['file_path']))

                await task

                # По хорошему все же надо тоже перевести в асинхронку + разделить создание текста и изменение в бд, может через селери делать как отдельный процесс.
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            else:
                # Если время ожидания истекло, делаем небольшую паузу перед следующей итерацией
                await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
