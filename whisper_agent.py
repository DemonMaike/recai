# Обрабатываем одно сообщение за раз. Если мы хотим обработать сразу 2 или 3, то мы меняем
# длину списка задач len(tasks) на нужное значение и можем выполнять обрабтку.
import asyncio
import os
import json

import aiohttp
import aio_pika
import aiofiles


async def create_file_from_whisper_container(path, content):
    async with aiofiles.open(path, "w") as file:
        output_format = []
        for sent in content["segments"]:
            speaker = sent.get("speaker", "Unknown Speaker")
            started = sent["start"]
            finised = sent["end"]
            text = sent["text"].strip()
            output_format.append(f"{speaker}\n{started} ... {finised}\n{text}\n")

        await file.write("\n".join(output_format))


async def handle_task(session, file_path):
    file_name = os.path.split(file_path)[-1]
    # нужно определять mime-type через mimetypes
    base_name, ext = os.path.splitext(file_name)
    out_file_path = f"static/text/{base_name}.txt"

    data = aiohttp.FormData()
    data.add_field(
        "file",
        open(file_path, "rb"),
        filename=file_name,
        content_type=f"audio/{ext.lstrip('.')}",
    )

    try:
        # Отправляем задачу в контейнер, в дальнейшем должен быть хаб.
        async with session.post(
            "http://127.0.0.1:5000/transcribe", data=data, timeout=500
        ) as response:
            if response.status == 200:
                result = await response.json()

                await create_file_from_whisper_container(out_file_path, result)
                print("Файл создан")
                return out_file_path

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
        queue = await channel.declare_queue("DiarizationQueue", durable=True)

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
                    body_data["way"].remove("DiarizationQueue")
                    body_data["file_path"] = out_path
                    updated_body = json.dumps(body_data)

                    # Отправка сообщения в AnswerQueue
                    await channel.default_exchange.publish(
                        aio_pika.Message(
                            body=updated_body.encode(),
                            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                        ),
                        routing_key="AnswerQueue",
                    )
                    print("Сообщение отправлено в MainQueue")
                    print(updated_body)

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
    print("Слушаю очередь DiarizationQueue")
    asyncio.run(main())
