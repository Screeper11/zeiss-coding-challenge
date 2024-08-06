import logging
import os

import feedparser
import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import ArxivQuery, ArxivResult
from ..schemas import ArxivSearchParams

router = APIRouter()
logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/arxiv", response_model=dict, tags=["arXiv"])
async def arxiv_endpoint(params: ArxivSearchParams, db: Session = Depends(get_db)):
    logger.info(f"Received arXiv request: {params}")

    if not any([params.author, params.title, params.journal]):
        raise HTTPException(status_code=400, detail="At least one of author, title, or journal must be provided")

    try:
        query_parts = []
        if params.author:
            query_parts.append(f"au:{params.author}")
        if params.title:
            query_parts.append(f"ti:{params.title}")
        if params.journal:
            query_parts.append(f"jr:{params.journal}")

        query = "+AND+".join(query_parts)
        url = f"{os.getenv('ARXIV_API_URL', 'https://export.arxiv.org/api/query')}?search_query={query}&start=0&max_results={params.max_results}&sortBy=relevance&sortOrder=descending"

        logger.info(f"Querying arXiv API with URL: {url}")
        response = requests.get(url)
        response.raise_for_status()

        feed = feedparser.parse(response.content)
        logger.info(f"Received {len(feed.entries)} results from arXiv API")

        query = ArxivQuery(
            query=feed.get("feed", {}).get("title", ""),
            status=response.status_code,
            num_results=min(int(feed.get("feed", {}).get("opensearch_totalresults", 0)), 100)
        )
        db.add(query)
        db.commit()
        db.refresh(query)

        for entry in feed.entries[:100]:
            result = ArxivResult(
                query_id=query.id,
                author=", ".join([author.get("name", "") for author in entry.get("authors", [])]),
                title=entry.get("title", ""),
                journal=entry.get("arxiv_journal_ref", "")
            )
            db.add(result)
        db.commit()
        logger.info(f"Stored query with id: {query.id}, num_results: {query.num_results}")

        return {"message": "Query results stored successfully", "query_id": query.id, "num_results": query.num_results}
    except requests.RequestException as e:
        logger.error(f"Error querying arXiv API: {str(e)}")
        raise HTTPException(status_code=503, detail="Error connecting to arXiv API")
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in arxiv_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
