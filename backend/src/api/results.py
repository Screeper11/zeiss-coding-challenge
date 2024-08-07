import logging
from typing import cast

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import ArxivResult, ArxivQuery
from ..schemas import PaginatedResponse, ResultResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/results", response_model=PaginatedResponse, tags=["Results"])
async def results_endpoint(
        page: int = Query(0, ge=0, lt=10, description="Page number (0-9)"),
        items_per_page: int = Query(10, const=True, description="Number of items per page (fixed at 10)"),
        db: Session = Depends(get_db)
):
    logger.info(f"Received request for results: page={page}")

    try:
        # Get the most recent query
        latest_query = db.query(ArxivQuery).order_by(ArxivQuery.id.desc()).first()

        if latest_query is None:
            return PaginatedResponse(total=0, page=page, items_per_page=items_per_page, items=[])

        total = cast(int, latest_query.num_results)
        results = db.query(ArxivResult).filter(ArxivResult.query_id == latest_query.id).order_by(
            ArxivResult.id.desc()).offset(page * items_per_page).limit(items_per_page).all()

        logger.info(f"Returning {len(results)} results out of {total}")
        return PaginatedResponse(
            total=min(total, 100),  # Limit total to 100
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
