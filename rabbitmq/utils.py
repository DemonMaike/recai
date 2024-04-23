import aio_pika
import json

# Вынести конфиг в корень проекта, добавить в .env
# юзера для кролика и прокинуть сюда.⏪


async def get_rabbit_connection():
    return await aio_pika.connect_robust("amqp://admin:admin@localhost/")


async def send_message_to_queue(task_id, file_path, queue_name):
    connection = await get_rabbit_connection()
    async with connection:
        channel = await connection.channel()    # Создание канала
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(
                    {"task_id": task_id, "file_path": file_path}).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=queue_name
        )

        # Добавить логирование ⏪
