import logging
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.src.api.arxiv import get_db
from backend.src.database import Base
from backend.src.main import app
from backend.src.models import ArxivQuery, ArxivResult

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Set up test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_create_arxiv_query(db_session):
    query = ArxivQuery(query="test query", status=200, num_results=10)
    db_session.add(query)
    db_session.commit()

    assert query.id is not None
    assert query.query == "test query"
    assert query.status == 200
    assert query.num_results == 10


def test_create_arxiv_result(db_session):
    query = ArxivQuery(query="test query", status=200, num_results=1)
    db_session.add(query)
    db_session.commit()

    result = ArxivResult(query_id=query.id, author="Test Author", title="Test Title", journal="Test Journal")
    db_session.add(result)
    db_session.commit()

    assert result.id is not None
    assert result.query_id == query.id
    assert result.author == "Test Author"
    assert result.title == "Test Title"
    assert result.journal == "Test Journal"


def test_arxiv_endpoint(client):
    response = client.post("/arxiv", json={
        "author": "Test Author",
        "title": "Test Title",
        "journal": "Test Journal",
        "max_results": 10
    })
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "query_id" in data
    assert "num_results" in data


def test_arxiv_endpoint_invalid_input(client):
    response = client.post("/arxiv", json={
        "author": "",
        "title": "",
        "journal": "",
        "max_results": 10
    })
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "At least one of author, title, or journal must be provided" in data["detail"]


def test_arxiv_endpoint_max_results(client):
    response = client.post("/arxiv", json={
        "author": "Test Author",
        "title": "Test Title",
        "max_results": 150  # Exceeds the limit of 100
    })
    assert response.status_code == 200
    data = response.json()
    assert data["num_results"] <= 100


def test_queries_endpoint_invalid_date_format(client):
    response = client.get("/queries", params={
        "query_start_time": "invalid-date",
        "query_end_time": datetime.now().isoformat(),
        "page": 0
    })
    assert response.status_code == 422  # Unprocessable Entity


def test_results_endpoint_invalid_page(client):
    response = client.get("/results", params={"page": -1})
    assert response.status_code == 422  # Unprocessable Entity


if __name__ == "__main__":
    pytest.main([__file__])
