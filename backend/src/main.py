import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from .api import arxiv, queries, results
from .database import create_tables


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_tables()
    yield


logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)
load_dotenv()

app = FastAPI(
    title="arXiv API",
    description="An API for searching and storing arXiv papers",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(arxiv.router)
app.include_router(queries.router)
app.include_router(results.router)

if __name__ == "__main__":
    import uvicorn
    import os

    uvicorn.run(app, host=os.getenv("BACKEND_API_HOST", "0.0.0.0"), port=int(os.getenv("BACKEND_API_PORT", "8000")))
