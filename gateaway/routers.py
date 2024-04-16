from fastapi import APIRouter


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


# загружаем аудио, пользователь должен получить объект Task в json, инициализируем в базе WEBSOCKET
@upload_router.post("/audio")
async def upload_audio():
    return


# загружаем текст, также получаем Task в json и инициализируем в базе WEBSOCKET
@upload_router.post("/text")
async def upload_text():
    return

    # Передать в очередь для полного пути, получаем данные из Task


@main_router.post("/start")
async def start():
    return


# Передать в очередь только на диаризацию.
@main_router.post("/start_diarization")
async def start_diarization():
    return


# передать в очередь только для подготовки репорта
@main_router.post("/start_create_report")
async def start_create_report():
    return


# ручки для тестов

@debug_router.post("/create_task")
async def create_task():
    return


@debug_router.post("/create_audio")
async def create_audio():
    return


@debug_router.post("/create_text")
async def create_text():
    return
