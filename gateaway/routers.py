from typing import AsyncGenerator
import copy

from fastapi import APIRouter, Depends, File as F, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import insert, select, update, delete
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

main_router = APIRouter(
    prefix="/main",
    tags=["Main"]
)

tasks_router = APIRouter(
    prefix="/task",
    tags=["Tasks"]
)

# может объеденить и внутри метода upload проверять аудио или текст ⏪


@upload_router.post("/audio")
async def upload_audio(file: UploadFile = F(...),
                       session: AsyncGenerator = Depends(get_async_session)):

    local_final_message = copy.deepcopy(final_message)

    if not File.is_audio(file.filename):
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = "File is not audio, please give an audio"

        return local_final_message

    out_filename = File.get_uuid_name(file.filename)
    path = f"static/audio/{out_filename}"
    local_final_message["status"] = Status.AUDIO_RECEIVED.value

    try:
        async with aiofiles.open(path, "wb") as out_file:
            while True:
                chunk = await file.read(File.CHUNK_SIZE)
                if not chunk:
                    break
                await out_file.write(chunk)

        stmt = insert(tasks).values(
            audio_path=path,
            status=Status.AUDIO_RECEIVED.value).returning(tasks.id)
        result = await session.execute(stmt)
        task_id = result.fetchone()[0]
        await session.commit()

        local_final_message["message"]["task_id"] = task_id
        local_final_message["message"]["info"] = out_filename

    except Exception as e:
        # отлвоить конкретные ошибки
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message


@upload_router.post("/text")
async def upload_text(file: UploadFile = F(...),
                      session: AsyncGenerator = Depends(get_async_session)):

    local_final_message = copy.deepcopy(final_message)

    if not File.is_text(file.filename):
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = "File is not text, please give an text"

        return local_final_message

    out_filename = File.get_uuid_name(file.filename)
    path = f"static/text/{out_filename}"
    local_final_message["status"] = Status.TEXT_RECEIVED.value

    try:
        async with aiofiles.open(path, "wb") as out_file:
            while True:
                chunk = await file.read(File.CHUNK_SIZE)
                if not chunk:
                    break
                await out_file.write(chunk)

        stmt = insert(tasks).values(
            text_path=path, status=Status.TEXT_RECEIVED.value).returning(tasks.id)
        result = await session.execute(stmt)
        task_id = result.fetchone()[0]
        await session.commit()

        local_final_message["message"]["task_id"] = task_id
        local_final_message["message"]["info"] = out_filename

    except Exception as e:
        # отлвоить конкретные ошибки
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message


# Cмотри ниже. Отправить в отдельную очередь чтобы агент следил
# за статусом.
@main_router.post("/start")
async def start():
    return


@main_router.post("/start_diarization")
async def start_diarization(task_id: int,
                            session: AsyncGenerator = Depends(get_async_session)):

    local_final_message = copy.deepcopy(final_message)

    local_final_message["message"]["task_id"] = task_id

    try:
        query = select(tasks).where(tasks.id == task_id)
        result = await session.execute(query)
        task = result.fetchone()[0]
        # проверить что не None, иначе вернуть сообщение чтобы загрузили audio
        file_path = task.audio_path

        stmt = update(tasks).where(tasks.id == task_id).values(
            status=Status.AUDIO_DIARIZATION_PROCESSING.value)
        await session.execute(stmt)
        await session.commit()

        local_final_message["status"] = Status.AUDIO_DIARIZATION_PROCESSING.value
        local_final_message["message"]["info"] = "File diaraizing"

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"

    else:
        await send_message_to_queue(task_id, file_path, "DiarizationQueue")

    return local_final_message


# передать в очередь только для подготовки репорта.
# Ориентируемся по статусам.
# все тоже самое что и в методе выше.
@main_router.post("/start_create_report")
async def start_create_report(task_id: int,
                              session: AsyncGenerator = Depends(get_async_session)):

    local_final_message = copy.deepcopy(final_message)

    local_final_message["message"]["task_id"] = task_id

    try:
        query = select(tasks).where(tasks.id == task_id)
        result = await session.execute(query)
        task = result.fetchone()[0]
        # Проверить что не None, иначе вернуть сообщение чтобы загрузили text
        file_path = task.text_path

        stmt = update(tasks).where(tasks.id == task_id).values(
            status=Status.AUDIO_DIARIZATION_PROCESSING.value)
        await session.execute(stmt)
        await session.commit()

        local_final_message["status"] = Status.LLM_ANALYSIS_PROCESSING.value
        local_final_message["message"]["info"] = "Creating report"

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"
    else:
        await send_message_to_queue(task_id, file_path, "LLMQueue")

    return local_final_message


@tasks_router.get("/{task_id}")
async def get_task(task_id: int,
                   session: AsyncGenerator = Depends(get_async_session)):

    local_final_message = copy.deepcopy(final_message)

    try:
        query = select(tasks).where(tasks.id == task_id)
        result = await session.execute(query)
        task = result.fetchone()[0]
        task_dict = task.__dict__.copy()

        local_final_message["status"] = task_dict.pop('status')
        local_final_message["message"]["task_id"] = task_dict.pop('id')
        local_final_message["message"]["info"] = task_dict

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["task_id"] = task_id
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message


@tasks_router.post("/create")
async def set_task(task: Task,
                   session: AsyncGenerator = Depends(get_async_session)):

    local_final_message = copy.deepcopy(final_message)

    try:
        stmt = insert(tasks).values(**task.dict()).returning(tasks.id)
        task_id = await session.execute(stmt)
        task_id = task_id.fetchone()[0]
        await session.commit()

        local_final_message["status"] = task.status
        local_final_message["message"]["task_id"] = task_id
        local_final_message["message"]["info"] = task.dict()

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message


@tasks_router.delete("/{task_id}")
async def delete_task(task_id: int,
                      session: AsyncGenerator = Depends(get_async_session)):

    local_final_message = copy.deepcopy(final_message)

    try:
        query = delete(tasks).where(tasks.id == task_id)
        await session.execute(query)
        await session.commit()

        local_final_message["status"] = Status.COMPLETED.value
        local_final_message["message"]["task_id"] = task_id
        local_final_message["message"]["info"] = f"Task {task_id} was deleted."

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["task_id"] = task_id
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message


# также задачи по юзеру когда сделаю юзеров! ⏪
