import logging

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import ArxivResult
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
        total = db.query(ArxivResult).count()
        results = db.query(ArxivResult).order_by(ArxivResult.id.desc()).offset(page * items_per_page).limit(items_per_page).all()

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
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in results_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
