import logging
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy.exc import SQLAlchemyError

from .api import arxiv, queries, results
from .database import Base, engine

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)
load_dotenv()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as e:
        logger.error(f"Failed to create tables: {str(e)}")
        raise
    yield
    engine.dispose()


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
