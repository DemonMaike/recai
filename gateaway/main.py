from database.database import create_db
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .routers import tasks_router, upload_router, main_router


app = FastAPI()

app.include_router(main_router)
app.include_router(upload_router)
app.include_router(tasks_router)

app.mount("/media", StaticFiles(directory="static"), name="media")


@app.on_event('startup')
async def startup_event():
    print("Creating db...")
    await create_db()
    print("DB created!")
