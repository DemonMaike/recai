import os
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse
from database import get_async_session
from models import Task as tasks, datetime
from sqlalchemy import insert, select
from schemas import Audio, Task, Text
from schemas import Status
import aiofiles
import uuid

CHUNK_SIZE = 5 * 1024 * 1024

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


# загружаем аудио, пользователь должен получить объект Task в json, инициализируем в базе
# добавить проверку на конкретные типы аудио, возвращать ошибку если че
@upload_router.post("/audio")
async def upload_audio(file: UploadFile = File(...),
                       session: AsyncGenerator = Depends(get_async_session)):

    filename, extantion = os.path.splitext(file.filename)
    out_filename = f"{uuid.uuid4()}{extantion}"
    # добавить проверку чтобы это был аудиоформат
    path = f"media/audio/{out_filename}"
    status = Status.AUDIO_RECEIVED
    final_message = {"task_id": None, "info": None}

    try:
        async with aiofiles.open(path, "wb") as out_file:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                await out_file.write(chunk)

        stmt = insert(tasks).values(
            audio_path=path).returning(tasks.id)
        result = await session.execute(stmt)
        task_id = result.fetchone()[0]
        await session.commit()
        final_message["task_id"] = task_id
        final_message["info"] = out_filename

    except Exception as e:  # отлвоить конкретные ошибки
        final_message["info"] = f"{e}"
        status = Status.ERROR

    return {"status": status, "message": final_message}

    # проверка на успешность, вернуть что не так
    # записать в базу
    # Объеденить с текстом?


# загружаем текст, также получаем Task в json и инициализируем в базе
# проверка типов, возвращать ошибку если не тот тип


@upload_router.post("/text")
async def upload_text(file: UploadFile = File(...),
                      AsyncGenerator=Depends(get_async_session)):
    return

# Передать в очередь для полного пути, получаем данные из Task
# Нужно привязать к файлу, когда отправляем в очередь, status, и по статусам
# оперировать агентами и очередями


@main_router.post("/start")
async def start():
    return


# Передать в очередь только на диаризацию.
# Ориентируемся по статусам.
@main_router.post("/start_diarization")
async def start_diarization():
    return


# передать в очередь только для подготовки репорта.
# Ориентируемся по статусам.
@main_router.post("/start_create_report")
async def start_create_report():
    return


# ручки для тестов

@debug_router.post("/create_task")
async def create_task(task: Task,
                      session: AsyncGenerator = Depends(get_async_session)):

    return {"status": task.status, "message": task.dict()}

# удалить, или пределать под проверку норм файла

# @debug_router.post("/audio")
# async def debug_upload_audio(file_path: Audio,
#                              session: AsyncGenerator = Depends(get_async_session)):
#     status = Status.AUDIO_RECEIVED
#     try:
#         stmt = insert(tasks).values(
#             audio_path=file_path.audio_path).returning(tasks.id)
#         result = await session.execute(stmt)
#         task_id = result.fetchone()[0]
#         await session.commit()
#         info = f"ID for task is {task_id}"
#     except Exception as e:
#         info = f"{e}"
#         status = Status.ERROR
#
#     return {"status": status, "message": info}


@debug_router.post("/text")
async def debug_upload_text(file_path: Text,
                            session: AsyncGenerator = Depends(get_async_session)):
    status = Status.TEXT_RECEIVED
    try:
        stmt = insert(tasks).values(
            text_path=file_path.text_path).returning(tasks.id)
        result = await session.execute(stmt)
        task_id = result.fetchone()[0]
        await session.commit()
        info = f"ID for task is {task_id}"
    except Exception as e:
        info = f"{e}"
        status = Status.ERROR

    return {"status": status, "message": info}
