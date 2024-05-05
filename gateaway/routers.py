from datetime import date
from typing import AsyncGenerator
import copy

from fastapi import APIRouter, Depends, File as F, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import EmailStr
from sqlalchemy import insert, select, update, delete
import aiofiles

from gateaway.schemas import Task
from gateaway.utils import Status, File, final_message
from gateaway.auth.schemas import UserRead
from gateaway.auth.settings import current_user
from database.utils import get_async_session
from database.models import Task as tasks, User
from rabbitmq.utils import send_message_to_queue


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

test_router = APIRouter(
    prefix="/test_tg",
    tags=["Test"]
)

@test_router.post('/start')
async def telegram_test(
    file: UploadFile = F(...),
    chat_id: str = Form(...),
    ):
    local_final_message = copy.deepcopy(final_message)
    local_final_message["status"] = Status.AUDIO_DIARIZATION_PROCESSING.value
    way = ["DiarizationQueue", "LLMQueue", "AnswerQueue"]

    out_filename = File.get_uuid_name(file.filename)
    path = f"static/audio/{out_filename}"

    try:
        async with aiofiles.open(path, "wb") as out_file:
            while True:
                chunk = await file.read(File.CHUNK_SIZE)
                if not chunk:
                    break
                await out_file.write(chunk)

        local_final_message["message"]["task_id"] = "telegram"
        local_final_message["message"]["info"] = out_filename
        await send_message_to_queue("telegram", way, path, "MainQueue", chat_id=int(chat_id))
    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message

# может объеденить и внутри метода upload проверять аудио или текст ⏪
# пройтись по поинтам и добавить проверку по статусу, где то может быть уже выполнена задача,
# а она все равно выполнится


@upload_router.post("/audio")
async def upload_audio(
    file: UploadFile = F(...),
    user: UserRead = Depends(current_user),
    session: AsyncGenerator = Depends(get_async_session),
):

    local_final_message = copy.deepcopy(final_message)

    if not File.is_audio(file.filename):
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"][
            "info"
        ] = "File is not audio, please give an audio"

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

        stmt = (
            insert(tasks)
            .values(
                user_id=user.id, audio_path=path, status=Status.AUDIO_RECEIVED.value
            )
            .returning(tasks.id)
        )
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
async def upload_text(
    file: UploadFile = F(...),
    user: UserRead = Depends(current_user),
    session: AsyncGenerator = Depends(get_async_session),
):

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

        stmt = (
            insert(tasks)
            .values(user_id=user.id, text_path=path, status=Status.TEXT_RECEIVED.value)
            .returning(tasks.id)
        )

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


@main_router.post("/start_diarization")
async def start_diarization(
    task_id: int, session: AsyncGenerator = Depends(get_async_session)
):

    local_final_message = copy.deepcopy(final_message)

    local_final_message["message"]["task_id"] = task_id

    try:
        query = select(tasks).where(tasks.id == task_id)
        result = await session.execute(query)
        task = result.fetchone()[0]
        if not task:
            raise HTTPException(
                status_code=400, detail="File is not upload, please upload file"
            )
        file_path = task.audio_path

        stmt = (
            update(tasks)
            .where(tasks.id == task_id)
            .values(status=Status.AUDIO_DIARIZATION_PROCESSING.value)
        )
        await session.execute(stmt)
        await session.commit()

        local_final_message["status"] = Status.AUDIO_DIARIZATION_PROCESSING.value
        local_final_message["message"]["info"] = "File diaraizing"

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"

    else:
        way = ["DiarizationQueue", "AnswerQueue"]
        await send_message_to_queue(task_id, way, file_path, "MainQueue")

    return local_final_message


@main_router.post("/start_create_report")
async def start_create_report(
    task_id: int, session: AsyncGenerator = Depends(get_async_session)
):

    local_final_message = copy.deepcopy(final_message)

    local_final_message["message"]["task_id"] = task_id

    try:
        query = select(tasks).where(tasks.id == task_id)
        result = await session.execute(query)
        task = result.fetchone()[0]
        if not task:
            raise HTTPException(
                status_code=400, detail="File is not upload, please upload file"
            )

        if not task.text_path:
            file_path = task.audio_path
        else:
            file_path = task.text_path

        stmt = (
            update(tasks)
            .where(tasks.id == task_id)
            .values(status=Status.AUDIO_DIARIZATION_PROCESSING.value)
        )
        await session.execute(stmt)
        await session.commit()

        local_final_message["message"]["info"] = "Creating report"

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"

    else:
        if (
            task.status == Status.TEXT_RECEIVED.value
            or task.status == Status.DIARIZATION_COMPLETED.value
        ):
            local_final_message["status"] = Status.LLM_ANALYSIS_PROCESSING.value
            way = ["LLMQueue", "AnswerQueue"]

        else:
            local_final_message["status"] = Status.AUDIO_DIARIZATION_PROCESSING.value
            way = ["DiarizationQueue", "LLMQueue", "AnswerQueue"]

        await send_message_to_queue(task_id, way, file_path, "MainQueue")

    return local_final_message


# На данный момент видно пароль, хоть и в хешшированнном виде, возможно скорректировать ⏪


@admin_router.get("/user/{email}")
async def see_user(
    email: EmailStr, session: AsyncGenerator = Depends(get_async_session)
):

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
async def del_user(
    email: EmailStr, session: AsyncGenerator = Depends(get_async_session)
):

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
async def set_task(task: Task, session: AsyncGenerator = Depends(get_async_session)):

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
async def get_task(task_id: int, session: AsyncGenerator = Depends(get_async_session)):

    local_final_message = copy.deepcopy(final_message)

    try:
        query = select(tasks).where(tasks.id == task_id)
        result = await session.execute(query)
        task = result.mapping().fetchone()[0]
        task_dict = task.copy()

        local_final_message["status"] = task_dict.pop("status")
        local_final_message["message"]["task_id"] = task_dict.pop("id")
        local_final_message["message"]["info"] = task_dict

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["task_id"] = task_id
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message


@admin_router.delete("/task/{task_id}")
async def delete_task(
    task_id: int, session: AsyncGenerator = Depends(get_async_session)
):

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
async def get_tasks_filter_status(
    status: Status, session: AsyncGenerator = Depends(get_async_session)
):  # получить перечень задач по cтатусу

    local_final_message = copy.deepcopy(final_message)

    try:
        query = select(tasks).where(tasks.status == status.value)
        result = await session.execute(query)
        tasks_with_status = result.scalars().all()
        tasks_with_status_as_dict = [task.__dict__ for task in tasks_with_status]

        local_final_message["status"] = Status.COMPLETED.value
        local_final_message["message"]["info"] = tasks_with_status_as_dict

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message


@admin_router.get("/tasks/user")
async def get_tasks_filter_user(
    email: EmailStr, session: AsyncGenerator = Depends(get_async_session)
):  # получить задачи по юзеру

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
async def get_tasks_filter_date(
    start_date: date,
    end_date: date,
    session: AsyncGenerator = Depends(get_async_session),
):

    if start_date > end_date:
        raise HTTPException(
            status_code=400, detail="Start date must be before end date"
        )

    local_final_message = copy.deepcopy(final_message)

    try:
        query = select(tasks).where(
            tasks.creation_date >= start_date, tasks.creation_date <= end_date
        )
        result = await session.execute(query)
        tasks_on_dates = result.scalars().all()
        tasks_on_dates_as_dict = [task.__dict__ for task in tasks_on_dates]

        local_final_message["status"] = Status.COMPLETED.value
        local_final_message["message"]["info"] = tasks_on_dates_as_dict

    except Exception as e:
        local_final_message["status"] = Status.ERROR.value
        local_final_message["message"]["info"] = f"{e}"

    return local_final_message


@user_router.get("/tasks")
async def get_user_tasks(
    user: UserRead = Depends(current_user),
    session: AsyncGenerator = Depends(get_async_session),
):

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


@user_router.delete("/task")
async def del_user_task(
    task_id: int,
    user: UserRead = Depends(current_user),
    session: AsyncGenerator = Depends(get_async_session),
):

    local_final_message = copy.deepcopy(final_message)

    try:

        query = select(tasks).where(tasks.id == task_id, tasks.user_id == user.id)
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
