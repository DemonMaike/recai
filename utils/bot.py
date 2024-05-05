from pyrogram.client import Client
from pyrogram import filters
import aiohttp


api_id = 27096153
api_hash = "0dcbfaadf99e28011431d68a43ddd576"
bot_token = "7168820996:AAFxs6fH1ZbnVt16UjOJAKW8pu4l9SG7pYo"

app = Client(
    "my_bot",
    api_id=api_id, api_hash=api_hash,
    bot_token=bot_token
)


@app.on_message(filters.audio)
async def test(client, message):
    try:
        # Загрузить аудио в память ?
        # отпарвить на ручку fastapi.
        # Убедиться что ручка загрузила файл, уведомить о начале работы.
        # Либо, возвращаем что за ошибка.

        file = await app.download_media(message, in_memory=True)
        file_name = file.name
        print(file_name)
        data = aiohttp.FormData()
        chat = message.chat.id

        data.add_field(
            "file",
            bytes(file.getbuffer()),
            filename=file_name,
            content_type=f"{file_name.lstrip('.')}",
        )

        data.add_field(
            "chat_id",
            chat,
        )

        async with aiohttp.ClientSession() as session:
            await session.post("http://91.218.251.26:40001/test_tg/start", data=data)

    except Exception as e:
        await message.reply(f"Ошибка при обработке.\n{e}")


app.run()
