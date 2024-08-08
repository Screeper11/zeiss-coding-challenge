from datetime import datetime
from typing import List

from pydantic import BaseModel


class QueryResponse(BaseModel):
    query: str
    timestamp: datetime
    status: int
    num_results: int


class ResultResponse(BaseModel):
    author: str
    title: str
    journal: str


class PaginatedResponse(BaseModel):
    total: int
    page: int
    items_per_page: int
    items: List[QueryResponse] | List[ResultResponse]


class ArxivSearchParams(BaseModel):
    author: str = ""
    title: str = ""
    journal: str = ""
    max_results: int = 100
