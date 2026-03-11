from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.database import engine, Base
import app.models  # noqa: F401 — register models on Base
from app.routers import auth, categories, tasks, pages

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Manager")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(tasks.router)
app.include_router(pages.router)
