import os
import asyncio
import json

from docx import Document
import aiohttp
import aio_pika
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
        "file", open(file_path, "rb"), filename=file_name, content_type=f"text/plain"
    )

    try:
        # Отправляем задачу в контейнер, в дальнейшем должен быть хаб.
        async with session.post(
            "http://127.0.0.1:5001/create_report", data=data, timeout=500
        ) as response:
            if response.status == 200:
                result = await response.json()

                await loop.run_in_executor(None, create_docx, out_name, result)
                print("Файл создан")
                return file_path

            else:
                print("Ошибка при обработке запроса.")
    except aiohttp.ClientError as e:
        print("Ошибка соединения: ", e)


async def main():
    connection = await aio_pika.connect_robust(
        "amqp://admin:admin@localhost/", loop=asyncio.get_event_loop()
    )

    async with connection:
        channel = await connection.channel()  # Создание канала
        await channel.set_qos(prefetch_count=1)
        queue = await channel.declare_queue("LLMQueue", durable=True)

        async with aiohttp.ClientSession() as session:
            async for message in queue:
                async with message.process():
                    print("Received message. Working...")
                    body_data = json.loads(message.body.decode())
                    print(body_data)

                    task = asyncio.create_task(
                        handle_task(session, body_data["file_path"])
                    )
                    out_path = await task

                    # Обновляем данные сообщения
                    body_data["way"].remove("LLMQueue")
                    body_data["file_path"] = out_path
                    updated_body = json.dumps(body_data)

                    # Отправка сообщения обратно в MainQueue
                    await channel.default_exchange.publish(
                        aio_pika.Message(
                            body=updated_body.encode(),
                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        ),
                        routing_key="MainQueue",
                    )
                    print("Сообщение отправлено в MainQueue")
                    print(updated_body)


if __name__ == "__main__":
    asyncio.run(main())
