from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class ArxivQuery(Base):
    __tablename__ = "arxiv_queries"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, index=True)
    timestamp = Column(DateTime(timezone=True), default=func.now())
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
