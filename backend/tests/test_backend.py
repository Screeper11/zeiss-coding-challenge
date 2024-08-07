from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.api.arxiv import get_db
from src.database import Base
from src.main import app
from src.models import ArxivQuery, ArxivResult

# Set up test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


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


def test_arxiv_endpoint():
    response = client.post("/arxiv", json={"author": "Test Author", "title": "Test Title", "journal": "Test Journal",
                                           "max_results": 10})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "query_id" in data
    assert "num_results" in data


def test_queries_endpoint():
    # Add some test data
    db = next(override_get_db())
    query1 = ArxivQuery(query="test query 1", status=200, num_results=10, timestamp=datetime.now())
    query2 = ArxivQuery(query="test query 2", status=200, num_results=5, timestamp=datetime.now() - timedelta(days=1))
    db.add(query1)
    db.add(query2)
    db.commit()

    response = client.get("/queries", params={
        "query_start_time": (datetime.now() - timedelta(days=2)).isoformat(),
        "query_end_time": datetime.now().isoformat(),
        "page": 0
    })
    if response.status_code != 200:
        print(f"Queries endpoint error: {response.status_code}")
        print(f"Response content: {response.content}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_results_endpoint():
    # Add some test data
    db = next(override_get_db())
    query = ArxivQuery(query="test query", status=200, num_results=2)
    db.add(query)
    db.commit()
    result1 = ArxivResult(query_id=query.id, author="Author 1", title="Title 1", journal="Journal 1")
    result2 = ArxivResult(query_id=query.id, author="Author 2", title="Title 2", journal="Journal 2")
    db.add(result1)
    db.add(result2)
    db.commit()

    response = client.get("/results", params={"page": 0})
    if response.status_code != 200:
        print(f"Results endpoint error: {response.status_code}")
        print(f"Response content: {response.content}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert data["items"][0]["author"] == "Author 2"  # Assuming reverse order
    assert data["items"][1]["author"] == "Author 1"


if __name__ == "__main__":
    pytest.main([__file__])
