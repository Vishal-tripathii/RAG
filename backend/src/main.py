import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.db import init_db
from src.routers import ask, health, upload
from src.vector_store import init_collection

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    force=True,
)
logging.getLogger("pdfminer").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_collection()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(health.router)
app.include_router(upload.router)
app.include_router(ask.router)
