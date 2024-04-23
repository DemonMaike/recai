from datetime import date, datetime
from typing import AsyncGenerator
import copy
import uuid

from fastapi import APIRouter, Depends, File as F, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import EmailStr
from sqlalchemy import insert, select, update, delete
import aiofiles

from auth.schemas import UserRead
from database import get_async_session
from models import Task as tasks, User
from .schemas import Task
from .utils import Status, File, final_message
from rabbitmq.utils import send_message_to_queue
from dependencies import current_user, admin


upload_router = APIRouter(
    prefix="/upload",
    tags=["Files"],
)

main_router = APIRouter(
    prefix="/main",
    tags=["Main"],
)

admin_router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)

user_router = APIRouter(
    prefix="/user",
    tags=["User"],
)


# может объеденить и внутри метода upload проверять аудио или текст ⏪


@upload_router.post("/audio")
async def upload_audio(file: UploadFile = F(...),
                       user: UserRead = Depends(current_user),
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
            user_id=user.id,
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
                      user: UserRead = Depends(current_user),
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

        stmt = insert(tasks).values(user_id=user.id,
                                    text_path=path,
                                    status=Status.TEXT_RECEIVED.value).returning(tasks.id)

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

# На данный момент видно пароль, хоть и в хешшированнном виде, возможно скорректироватть ⏪


@admin_router.get("/user/{email}")
async def see_user(email: EmailStr,
                   session: AsyncGenerator = Depends(get_async_session)):

    local_final_message = copy.deepcopy(final_message)

    try:
        query = select(User).where(User.email == email)
        result = await session.execute(query)
        user = result.scalars().first()
        user_data = copy.copy(user)

        local_final_message["status"] = Status.COMPLETED.value
        local_final_message["message"]["info"] = user_data

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message


@admin_router.delete("/user/{email}")
async def del_user(email: EmailStr,
                   session: AsyncGenerator = Depends(get_async_session)):

    local_final_message = copy.deepcopy(final_message)

    try:
        stmt = delete(User).where(User.c.email == email)
        await session.execute(stmt)
        await session.commit()

        local_final_message["status"] = Status.COMPLETED.value
        local_final_message["message"]["info"] = f"User {email} is deleted."

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message


@admin_router.post("/task")
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


@admin_router.get("/task/{task_id}")
async def get_task(task_id: int,
                   session: AsyncGenerator = Depends(get_async_session)):

    local_final_message = copy.deepcopy(final_message)

    try:
        query = select(tasks).where(tasks.id == task_id)
        result = await session.execute(query)
        task = result.mapping().fetchone()[0]
        task_dict = task.copy()

        local_final_message["status"] = task_dict.pop('status')
        local_final_message["message"]["task_id"] = task_dict.pop('id')
        local_final_message["message"]["info"] = task_dict

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["task_id"] = task_id
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message


@admin_router.delete("/task/{task_id}")
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


@admin_router.get("/tasks/status")
async def get_tasks_filter_status(status: Status,
                                  session: AsyncGenerator = Depends(get_async_session)):  # получить перечень задач по cтатусу

    local_final_message = copy.deepcopy(final_message)

    try:
        query = select(tasks).where(tasks.status == status.value)
        result = await session.execute(query)
        tasks_with_status = result.scalars().all()
        tasks_with_status_as_dict = [
            task.__dict__ for task in tasks_with_status]

        local_final_message["status"] = Status.COMPLETED.value
        local_final_message["message"]["info"] = tasks_with_status_as_dict

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message


@admin_router.get("/tasks/user")
async def get_tasks_filter_user(email: EmailStr,
                                session: AsyncGenerator = Depends(get_async_session)):  # получить задачи по юзеру

    local_final_message = copy.deepcopy(final_message)

    try:
        query = select(User).where(User.email == email)
        result = await session.execute(query)
        user_id = result.scalar().id

        final_query = select(tasks).where(tasks.user_id == user_id)
        final_result = await session.execute(final_query)
        users_tasks = final_result.scalars().all()
        users_tasks_as_dict = [task.__dict__ for task in users_tasks]

        local_final_message["status"] = Status.COMPLETED.value
        local_final_message["message"]["info"] = users_tasks_as_dict

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message


# Стоит скорректировать вермя на работу с конкретной тайм-зоной, иначе путаница, нужно везде переделать работу с ru таймзоной ⏪
@admin_router.get("/tasks/date")
async def get_tasks_filter_date(start_date: date,
                                end_date: date,
                                session: AsyncGenerator = Depends(get_async_session)):  # получить задачи по дата начало/конец

    if start_date > end_date:
        raise HTTPException(status_code=400,
                            detail="Start date must be before end date")

    local_final_message = copy.deepcopy(final_message)

    try:
        query = select(tasks).\
            where(tasks.creation_date >= start_date,
                  tasks.creation_date <= end_date)
        result = await session.execute(query)
        tasks_on_dates = result.scalars().all()
        tasks_on_dates_as_dict = [task.__dict__ for task in tasks_on_dates]

        local_final_message["status"] = Status.COMPLETED.value
        local_final_message["message"]["info"] = tasks_on_dates_as_dict

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message

# Подумать как польучать пользователя динамически из данных авторизации, использования запроса на прямую и расшифровывать куки,
# или что то подобное ⏪


@user_router.get("/tasks")
async def get_user_tasks(user: UserRead = Depends(current_user),
                         session: AsyncGenerator = Depends(get_async_session)):

    local_final_message = copy.deepcopy(final_message)

    try:
        query = select(tasks).where(tasks.user_id == user.id)
        result = await session.execute(query)
        current_users_tasks = result.scalars().all()

        tasks_as_dicts = [task.__dict__ for task in current_users_tasks]

        local_final_message["status"] = Status.COMPLETED.value
        local_final_message["message"]["info"] = tasks_as_dicts

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message


# юзер может удалить свою задачу, но проверять что это задача текущего юзера.
@user_router.delete("/task")
async def del_user_task(task_id: int,
                        user: UserRead = Depends(current_user),
                        session: AsyncGenerator = Depends(get_async_session)):

    local_final_message = copy.deepcopy(final_message)

    try:

        query = select(tasks).where(tasks.id == task_id,
                                    tasks.user_id == user.id)
        query_result = await session.execute(query)
        task = query_result.scalars().first()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        stmt = delete(tasks).where(tasks.id == task_id)
        await session.execute(stmt)
        await session.commit()

        local_final_message["status"] = Status.COMPLETED.value
        local_final_message["message"]["task_id"] = task_id
        local_final_message["message"]["info"] = "Message was deleted."

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message
