import logging

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import and_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from .utils import get_db
from ..models import ArxivResult, ArxivQuery
from ..schemas import PaginatedResponse, ResultResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_latest_query(db: Session):
    return db.query(ArxivQuery).order_by(ArxivQuery.id.desc()).first()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_results(db: Session, query_id: int, skip: int, limit: int):
    return db.query(ArxivResult).filter(and_(ArxivResult.query_id == query_id)).order_by(
        ArxivResult.id.desc()).offset(skip).limit(limit).all()


@router.get("/results", response_model=PaginatedResponse, tags=["Results"])
async def results_endpoint(
        page: int = Query(0, ge=0, lt=10, description="Page number (0-9)"),
        items_per_page: int = Query(10, const=True, description="Number of items per page (fixed at 10)"),
        db: Session = Depends(get_db)
):
    logger.info(f"Received request for results: page={page}")

    try:
        latest_query: ArxivQuery | None = fetch_latest_query(db)

        if latest_query is None:
            return PaginatedResponse(total=0, page=page, items_per_page=items_per_page, items=[])

        total = latest_query.num_results
        results = fetch_results(db, latest_query.id, page * items_per_page, items_per_page)

        logger.info(f"Returning {len(results)} results out of {total}")
        return PaginatedResponse(
            total=min(total, 100),
            page=page,
            items_per_page=items_per_page,
            items=[ResultResponse(
                author=result.author,
                title=result.title,
                journal=result.journal
            ) for result in results]
        )
    except SQLAlchemyError as error:
        logger.error(f"Database error: {str(error)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as error:
        logger.error(f"Unexpected error in results_endpoint: {str(error)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
