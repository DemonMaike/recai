import uuid
from fastapi_users import FastAPIUsers
from auth.manager import get_user_manager
from models import User
from database import create_db
from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles
from .routers import tasks_router, upload_router, main_router
from auth.utils import auth_backand
from auth.schemas import UserRead, UserCreate

# Auth
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backand],
)

current_user = fastapi_users.current_user()


app = FastAPI()
app.include_router(
    fastapi_users.get_auth_router(auth_backand),
    prefix="/auth",
    tags=["auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(main_router)
app.include_router(upload_router, dependencies=[Depends(current_user)])
app.include_router(tasks_router, dependencies=[Depends(current_user)])


app.mount("/media", StaticFiles(directory="static"), name="media")


@app.on_event('startup')
async def startup_event():
    print("Creating db...")
    await create_db()
    print("DB created!")
