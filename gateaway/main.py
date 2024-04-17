from fastapi import FastAPI
from routers import debug_router, upload_router, main_router
from fastapi.staticfiles import StaticFiles
app = FastAPI()

app.include_router(debug_router)
app.include_router(upload_router)
app.include_router(main_router)


app.mount("/media", StaticFiles(directory="media"), name="media")
