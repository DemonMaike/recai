import asyncio
import json

from aio_pika import Message, connect
from aio_pika import IncomingMessage
from config import RABBIT_ADMIN, RABBIT_ADMIN_PASS, RABBIT_HOST, RABBIT_QUEUE_PORT


async def main():
    connection = await connect(f"amqp://{RABBIT_ADMIN}:{RABBIT_ADMIN_PASS}@{RABBIT_HOST}:{RABBIT_QUEUE_PORT}/")
    channel = await connection.channel()  # Создаем канал связи

    exchange = channel.default_exchange
    main_queue = await channel.declare_queue('MainQueue', durable=True)

    async def on_message(message: IncomingMessage):
        async with message.process():
            data = json.loads(message.body.decode())
            target_queue_name = data['way'][0]

            await exchange.publish(
                Message(
                    body=message.body,
                    expiration=message.expiration,
                    priority=message.priority),
                routing_key=target_queue_name
            )
            print(f"Перенаправлено в {target_queue_name}")

    await main_queue.consume(on_message)
    print("Основной агент запущен и слушает очередь 'main'.")

    await asyncio.Future()  # Запускаем бесконечный цикл

if __name__ == '__main__':
    asyncio.run(main())
