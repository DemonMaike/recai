# Обрабатываем одно сообщение за раз. Если мы хотим обработать сразу 2 или 3, то мы меняем
# длину списка задач len(tasks) на нужное значение и можем выполнять обрабтку.
import asyncio
import os
import aiohttp
import pika
from pika.adapters.blocking_connection import BlockingChannel


async def handle_task(session, file_path):
    file_name = os.path.split(file_path)[-1]
    # нужно определять mime-type через mimetypes
    _, ext = os.path.splitext(file_name)

    data = aiohttp.FormData()
    data.add_field(
        'file',
        open(file_path, 'rb'),
        filename=file_name,
        content_type=f"audio/{ext}")

    try:
        # Отправляем задачу на один из контейнеров
        async with session.post('http://127.0.0.1:5000/transcribe', data=data) as response:
            if response.status == 200:
                result = await response.json()
                print("Результат транскрибации: ", result)
            else:
                print("Ошибка при обработке запроса.")
    except aiohttp.ClientError as e:
        print("Ошибка соединения: ", e)


async def main():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='DiarizationQueue')

    tasks = []

    async with aiohttp.ClientSession() as session:
        for method_frame, properties, body in channel.consume('DiarizationQueue'):
            # Запускаем обработку задачи асинхронно
            task = asyncio.create_task(handle_task(session, body['file_path']))
            tasks.append(task)
            if len(tasks) >= 1:  # Предполагаем, что у нас есть 1 контейнер
                break

        # Ожидаем завершения всех задач
        await asyncio.gather(*tasks)

        # Подтверждаем обработку сообщений
        for task in tasks:
            channel.basic_ack(delivery_tag=task.result())

    connection.close()

if __name__ == '__main__':
    asyncio.run(main())
