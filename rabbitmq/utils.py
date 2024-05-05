import aio_pika
import json
from config import RABBIT_ADMIN, RABBIT_ADMIN_PASS, RABBIT_HOST, RABBIT_QUEUE_PORT


async def get_rabbit_connection():
    return await aio_pika.connect_robust(f"amqp://{RABBIT_ADMIN}:{RABBIT_ADMIN_PASS}@{RABBIT_HOST}:{RABBIT_QUEUE_PORT}/")


async def send_message_to_queue(task_id, way, file_path, queue_name, **kwargs):
    connection = await get_rabbit_connection()
    message_data = {
        "task_id": task_id,
        "way": way,
        "file_path": file_path
    }
    message_data.update(kwargs)

    async with connection:
        channel = await connection.channel()    # Создание канала
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message_data).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=queue_name
        )
        # Добавить логирование ⏪
