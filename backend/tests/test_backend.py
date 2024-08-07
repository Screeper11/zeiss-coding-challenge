import logging
import os

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


def remove_db_file():
    if os.path.exists("./test.db"):
        try:
            os.remove("./test.db")
            logger.info("Removed test.db file")
        except PermissionError:
            logger.warning("Unable to remove test.db file. It may still be in use.")


@pytest.fixture(scope="session", autouse=True)
def clean_up(request):
    def finalizer():
        TestingSessionLocal.close_all()
        engine.dispose()
        remove_db_file()

    request.addfinalizer(finalizer)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    # noinspection PyUnresolvedReferences
    app.dependency_overrides[get_db] = db_session
    with TestClient(app) as c:
        yield c


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


if __name__ == "__main__":
    pytest.main([__file__])
