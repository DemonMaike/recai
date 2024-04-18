from typing import AsyncGenerator

from fastapi import APIRouter, Depends, File as F, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import insert, select, update
import aiofiles

from database.database import get_async_session
from database.models import Task as tasks
from .schemas import Task
from .utils import Status, File, final_message
from rabbitmq.utils import send_message_to_queue


upload_router = APIRouter(
    prefix="/upload",
    tags=["Files"],
)

debug_router = APIRouter(
    prefix="/debug",
    tags=["Debug"],
)

main_router = APIRouter(
    prefix="/main",
    tags=["Main"]
)

# может объеденить и внутри метода upload проверять аудио или текст ⏪


@upload_router.post("/audio")
async def upload_audio(file: UploadFile = F(...),
                       session: AsyncGenerator = Depends(get_async_session)):

    if not File.is_audio(file.filename):
        final_message["status"] = Status.ERROR
        final_message["message"]["info"] = "File is not audio, please give an audio"

        return final_message

    out_filename = File.get_uuid_name(file.filename)
    path = f"static/audio/{out_filename}"
    final_message["status"] = Status.AUDIO_RECEIVED

    try:
        async with aiofiles.open(path, "wb") as out_file:
            while True:
                chunk = await file.read(File.CHUNK_SIZE)
                if not chunk:
                    break
                await out_file.write(chunk)

        stmt = insert(tasks).values(
            audio_path=path).returning(tasks.id)
        result = await session.execute(stmt)
        task_id = result.fetchone()[0]
        await session.commit()

        final_message["message"]["task_id"] = task_id
        final_message["message"]["info"] = out_filename

    except Exception as e:
        # отлвоить конкретные ошибки
        final_message["status"] = Status.ERROR
        final_message["message"]["info"] = f"{e}"

    return final_message


@upload_router.post("/text")
async def upload_text(file: UploadFile = F(...),
                      session: AsyncGenerator = Depends(get_async_session)):
    if not File.is_text(file.filename):
        final_message["status"] = Status.ERROR
        final_message["message"]["info"] = "File is not text, please give an text"

        return final_message

    out_filename = File.get_uuid_name(file.filename)
    path = f"static/text/{out_filename}"
    final_message["status"] = Status.TEXT_RECEIVED

    try:
        async with aiofiles.open(path, "wb") as out_file:
            while True:
                chunk = await file.read(File.CHUNK_SIZE)
                if not chunk:
                    break
                await out_file.write(chunk)

        stmt = insert(tasks).values(
            text_path=path).returning(tasks.id)
        result = await session.execute(stmt)
        task_id = result.fetchone()[0]
        await session.commit()

        final_message["message"]["task_id"] = task_id
        final_message["message"]["info"] = out_filename

    except Exception as e:
        # отлвоить конкретные ошибки
        final_message["status"] = Status.ERROR
        final_message["message"]["info"] = f"{e}"

    return final_message


# Cмотри ниже. Отправить в отдельную очередь чтобы агент следил
# за статусом.
@main_router.post("/start")
async def start():
    return


# Передать в очередь только на диаризацию.
# Передать task_id, получить из базы путь к файлу,
# передать в очередь task_id и путь к файлу, агент конкретной задачи
# пишет путь файла в бд.
@main_router.post("/start_diarization")
async def start_diarization(task_id: int,
                            session: AsyncGenerator = Depends(get_async_session)):
    final_message["message"]["task_id"] = task_id

    try:
        query = select(tasks).where(tasks.id == task_id)
        result = await session.execute(query)
        task = result.fetchone()[0]
        file_path = task.audio_path

        await send_message_to_queue(task_id, file_path, "DiarizationQueue")

        stmt = update(tasks).where(tasks.id == task_id).values(
            status=Status.AUDIO_DIARIZATION_PROCESSING.value)
        await session.execute(stmt)
        await session.commit()

        final_message["status"] = Status.AUDIO_DIARIZATION_PROCESSING
        final_message["message"]["info"] = "File diaraizing"

    except Exception as e:
        final_message["status"] = Status.ERROR
        final_message["message"]["info"] = f"{e}"

    return final_message


# передать в очередь только для подготовки репорта.
# Ориентируемся по статусам.
# все тоже самое что и в методе выше.
@main_router.post("/start_create_report")
async def start_create_report():
    return


# ручки для тестов

@debug_router.post("/create_task")
async def create_task(task: Task,
                      session: AsyncGenerator = Depends(get_async_session)):

    return {"status": task.status, "message": task.dict()}
