from fastapi import Depends, FastAPI
from fastapi.staticfiles import StaticFiles


from database.utils import create_db
from gateaway.routers import (upload_router, main_router,
                              admin_router, user_router, test_router)
from gateaway.auth.utils import auth_backand
from gateaway.auth.schemas import UserRead, UserCreate
from gateaway.auth.settings import fastapi_users, current_user, admin


app = FastAPI()
app.include_router(
    fastapi_users.get_auth_router(auth_backand),
    prefix="/auth/jwt",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth/jwt",
    tags=["Auth"],
)


app.include_router(main_router,
                   dependencies=[Depends(current_user)])
app.include_router(upload_router,
                   dependencies=[Depends(current_user)])
app.include_router(admin_router,
                   dependencies=[Depends(admin)])
app.include_router(user_router,
                   dependencies=[Depends(current_user)])
app.include_router(test_router)

app.mount("/media", StaticFiles(directory="static"), name="media")



@app.on_event('startup')
async def startup_event():
    print("Creating db...")
    await create_db()
    print("DB created!")
