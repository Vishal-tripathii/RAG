from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.db import init_db
from src.routers import health, upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(health.router)
app.include_router(upload.router)
