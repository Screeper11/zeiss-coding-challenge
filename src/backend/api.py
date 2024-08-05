import logging
from datetime import datetime, timezone
from typing import List, Optional

import feedparser
import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

from config import settings

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class ArxivQuery(Base):
    __tablename__ = "arxiv_queries"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(Integer)
    num_results = Column(Integer)

    results = relationship("ArxivResult", back_populates="query")


class ArxivResult(Base):
    __tablename__ = "arxiv_results"

    id = Column(Integer, primary_key=True, index=True)
    query_id = Column(Integer, ForeignKey('arxiv_queries.id'), index=True)
    author = Column(String)
    title = Column(String)
    journal = Column(String)

    query = relationship("ArxivQuery", back_populates="results")


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="arXiv API",
    description="An API for searching and storing arXiv papers",
    version="1.0.0"
)


class QueryResponse(BaseModel):
    query: str
    timestamp: datetime
    status: int
    num_results: int


class ResultResponse(BaseModel):
    author: str
    title: str
    journal: str


class ArxivSearchParams(BaseModel):
    author: str = ""
    title: str = ""
    journal: str = ""
    max_results: int = 8


def search_arxiv(author: str = "", title: str = "", journal: str = "", max_results: int = 8):
    query_parts = []
    if author:
        query_parts.append(f"au:{author}")
    if title:
        query_parts.append(f"ti:{title}")
    if journal:
        query_parts.append(f"jr:{journal}")

    if not query_parts:
        raise ValueError("At least one of author, title, or journal must be provided")

    query = "+AND+".join(query_parts)
    url = f"{settings.ARXIV_API_URL}?search_query={query}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"

    logger.info(f"Querying arXiv API with URL: {url}")
    response = requests.get(url)
    response.raise_for_status()

    feedparser.mixin._FeedParserMixin.namespaces["http://a9.com/-/spec/opensearch/1.1/"] = "opensearch"
    feedparser.mixin._FeedParserMixin.namespaces["http://arxiv.org/schemas/atom"] = "arxiv"
    feed = feedparser.parse(response.content)
    logger.info(f"Received {len(feed.entries)} results from arXiv API")
    return feed, response


@app.post("/arxiv", response_model=dict, tags=["arXiv"])
async def arxiv_endpoint(params: ArxivSearchParams):
    """
    Search arXiv and store results in the database.

    - **author**: Author name to search for
    - **title**: Title to search for
    - **journal**: Journal to search for
    - **max_results**: Maximum number of results to return (default: 8)
    """
    logger.info(f"Received arXiv request: {params}")

    if not any([params.author, params.title, params.journal]):
        raise HTTPException(status_code=400, detail="At least one of author, title, or journal must be provided")

    try:
        feed, response = search_arxiv(params.author, params.title, params.journal, params.max_results)
        logger.info(f"arXiv API response status: {response.status_code}")

        db = SessionLocal()
        try:
            query = ArxivQuery(
                query=feed.get("feed", {}).get("title", ""),
                status=response.status_code,
                num_results=int(feed.get("feed", {}).get("opensearch_totalresults", 0))
            )
            db.add(query)
            db.commit()
            db.refresh(query)

            for entry in feed.entries:
                result = ArxivResult(
                    query_id=query.id,
                    author=", ".join([author.get("name", "") for author in entry.get("authors", [])]),
                    title=entry.get("title", ""),
                    journal=entry.get("arxiv_journal_ref", "")
                )
                db.add(result)
            db.commit()
            logger.info(f"Stored query with id: {query.id}, num_results: {query.num_results}")

            return {"message": "Query results stored successfully", "query_id": query.id,
                    "num_results": query.num_results}
        finally:
            db.close()
    except requests.RequestException as e:
        logger.error(f"Error querying arXiv API: {str(e)}")
        raise HTTPException(status_code=503, detail="Error connecting to arXiv API")
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error occurred")
    except Exception as e:
        logger.error(f"Unexpected error in arxiv_endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


@app.get("/queries", response_model=List[QueryResponse], tags=["Queries"])
async def queries_endpoint(
        query_start_time: datetime = Query(..., description="Start time for query range"),
        query_end_time: Optional[datetime] = Query(None, description="End time for query range")
):
    """
    Retrieve queries from the database based on timestamp range.

    - **query_start_time**: Start time for the query range (required)
    - **query_end_time**: End time for the query range (optional)
    """
    logger.info(f"Received request for queries: start={query_start_time}, end={query_end_time}")
    db = SessionLocal()
    try:
        query = db.query(ArxivQuery).filter(ArxivQuery.timestamp >= query_start_time)
        if query_end_time:
            query = query.filter(ArxivQuery.timestamp <= query_end_time)
        results = query.all()
        logger.info(f"Returning {len(results)} queries")
        return [QueryResponse(
            query=result.query,
            timestamp=result.timestamp,
            status=result.status,
            num_results=result.num_results
        ) for result in results]
    finally:
        db.close()


@app.get("/results", response_model=List[ResultResponse], tags=["Results"])
async def results_endpoint(
        page: int = Query(0, ge=0, description="Page number"),
        items_per_page: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """
    Retrieve stored query results with pagination.

    - **page**: Page number (default: 0)
    - **items_per_page**: Number of items per page (default: 10, max: 100)
    """
    logger.info(f"Received request for results: page={page}, items_per_page={items_per_page}")
    db = SessionLocal()
    try:
        results = db.query(ArxivResult).order_by(ArxivResult.id.desc()).offset(page * items_per_page).limit(
            items_per_page).all()
        logger.info(f"Returning {len(results)} results")
        return [ResultResponse(
            author=result.author,
            title=result.title,
            journal=result.journal
        ) for result in results]
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.BACKEND_API_HOST, port=settings.BACKEND_API_PORT)
