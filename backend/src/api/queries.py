import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from .utils import get_db
from ..models import ArxivQuery
from ..schemas import PaginatedResponse, QueryResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def fetch_queries(db: Session, query_start_time: datetime, query_end_time: Optional[datetime], skip: int, limit: int):
    query = db.query(ArxivQuery).filter(ArxivQuery.timestamp >= query_start_time)
    if query_end_time:
        query = query.filter(ArxivQuery.timestamp <= query_end_time)
    return query.order_by(ArxivQuery.timestamp.desc()).offset(skip).limit(limit).all()


@router.get("/queries", response_model=PaginatedResponse, tags=["Queries"])
async def queries_endpoint(
        query_start_time: datetime = Query(..., description="Start time for query range"),
        query_end_time: Optional[datetime] = Query(None, description="End time for query range"),
        page: int = Query(0, ge=0, lt=10, description="Page number (0-9)"),
        items_per_page: int = Query(10, const=True, description="Number of items per page (fixed at 10)"),
        db: Session = Depends(get_db)
):
    logger.info(f"Received request for queries: start={query_start_time}, end={query_end_time}, page={page}")

    try:
        query = db.query(ArxivQuery).filter(ArxivQuery.timestamp >= query_start_time)
        if query_end_time:
            query = query.filter(ArxivQuery.timestamp <= query_end_time)

        total = query.count()
        results = fetch_queries(db, query_start_time, query_end_time, page * items_per_page, items_per_page)

        logger.info(f"Returning {len(results)} queries out of {total}")
        return PaginatedResponse(
            total=min(total, 100),  # Limit total to 100
            page=page,
            items_per_page=items_per_page,
            items=[QueryResponse(
                query=result.query,
                timestamp=result.timestamp,
                status=result.status,
                num_results=result.num_results
            ) for result in results]
        )
    except SQLAlchemyError as error:
        logger.error(f"Database error: {str(error)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as error:
        logger.error(f"Unexpected error in queries_endpoint: {str(error)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
