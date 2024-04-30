# Обрабатываем одно сообщение за раз. Если мы хотим обработать сразу 2 или 3, то мы меняем
# длину списка задач len(tasks) на нужное значение и можем выполнять обрабтку.
import asyncio
import os
import json

import aiohttp
import pika
import aiofiles


async def create_file_from_whisper_container(path, content):
    async with aiofiles.open(path, "w") as file:
        output_format = []
        for sent in content["segments"]:
            speaker = sent.get("speaker", "Unknown Speaker")
            started = sent["start"]
            finised = sent["end"]
            text = sent["text"].strip()
            output_format.append(
                f"{speaker}\n{started} ... {finised}\n{text}\n")

        await file.write("\n".join(output_format))


async def handle_task(session, file_path):
    file_name = os.path.split(file_path)[-1]
    # нужно определять mime-type через mimetypes
    base_name, ext = os.path.splitext(file_name)
    out_file_path = f"static/text/{base_name}.txt"

    data = aiohttp.FormData()
    data.add_field(
        'file',
        open(file_path, 'rb'),
        filename=file_name,
        content_type=f"audio/{ext.lstrip('.')}")

    try:
        # Отправляем задачу в контейнер, в дальнейшем должен быть хаб.
        async with session.post('http://127.0.0.1:5000/transcribe',
                                data=data, timeout=500) as response:
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
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        'localhost', 5672, '/', pika.PlainCredentials("admin", "admin")))
    channel = connection.channel()
    channel.queue_declare(queue='DiarizationQueue', durable=True)

    async with aiohttp.ClientSession() as session:
        while True:
            method_frame, properties, body = next(channel.consume(
                'DiarizationQueue', inactivity_timeout=None))
            if method_frame:
                print("Recived message. Working...")
                body_decoded = body.decode("utf-8")
                body_data = json.loads(body_decoded)

                task = asyncio.create_task(
                    handle_task(session, body_data['file_path']))
                out_path = await task
                # По хорошему все же надо тоже перевести в асинхронку + разделить создание текста и изменение в бд, может через селери делать как отдельный процесс.

                # изменить тело сообщения согласно текущему процессу.
                body_data["way"].remove("DiarizationQueue")
                body_data["file_path"] = out_path

                updated_body = json.dumps(body_data)
                channel.basic_publish(exchange='',
                                      routing_key='MainQueue',
                                      body=updated_body,
                                      properties=pika.BasicProperties(
                                          delivery_mode=2,
                                      ))
                print("Сообщение отправлено в MainQueue")
                channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                # Записать новый статус в бд

            else:
                # Если время ожидания истекло, делаем небольшую паузу перед следующей итерацией
                await asyncio.sleep(1)

if __name__ == '__main__':
    print("слушаю очередь DiarizationQueue")
    asyncio.run(main())
