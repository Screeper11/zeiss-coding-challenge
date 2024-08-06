import logging
from datetime import datetime, timezone, timedelta
import math
import os

import httpx
from dotenv import load_dotenv
from fasthtml.common import *

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)
load_dotenv()

app, rt = fast_app()
Favicon("assets/favicon.ico", "assets/favicon.ico")

API_URL = os.getenv("BACKEND_API_URL", "http://api:8000")

try:
    with open("assets/styles.css", 'r') as file:
        styles_css = file.read()
except (FileNotFoundError, IOError) as e:
    logger.error(f"Error reading CSS file: {e}")
    styles_css = ""


def query_form():
    def form_inputs():
        return [
            Label("Author", Input(type="text", name="author", placeholder="Enter author name")),
            Label("Title", Input(type="text", name="title", placeholder="Enter paper title")),
            Label("Journal", Input(type="text", name="journal", placeholder="Enter journal name")),
        ]

    return Form(
        H2("arXiv Query Parameters"),
        *form_inputs(),
        Button("Search", type="submit"),
        id="search-form",
        cls="search-form",
        hx_post="/search",
        hx_target="#results",
        hx_swap="innerHTML",
        hx_include="[name='author'],[name='title'],[name='journal']"
    )


def results_list(results_data, page=1):
    if not results_data or results_data['total'] == 0:
        return P("No results found.")

    total_results = results_data['total']
    items_per_page = results_data['items_per_page']
    current_page = results_data['page'] + 1  # API uses 0-based indexing, we use 1-based
    results = results_data['items']

    result_list = Ul(*[
        Li(
            H3(result['title']),
            P(f"Author: {result['author']}"),
            P(f"Journal: {result['journal']}")
        ) for result in results
    ])

    total_pages = min(math.ceil(total_results / items_per_page), 10)  # Maximum 10 pages

    pagination = Div(
        *(
            A(
                str(i),
                hx_get=f"/search?page={i}",
                hx_target="#results",
                cls="page-link active" if i == current_page else "page-link"
            )
            for i in range(1, total_pages + 1)
        ),
        cls="pagination"
    )

    return Div(
        P(f"Showing results {(current_page - 1) * items_per_page + 1}-{min(current_page * items_per_page, total_results)} of {total_results}"),
        result_list,
        pagination
    )


@rt("/")
def get():
    return Html(
        Head(
            Title("ZEISS Coding Challenge | Bence Papp"),
            Link(rel="stylesheet", href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css"),
            Style(styles_css),
            Script(src="https://unpkg.com/htmx.org@1.9.10")
        ),
        Body(
            Main(
                Div(
                    H1("ZEISS Coding Challenge"),
                    P("Made by Bence Papp", cls="subtitle"),
                    query_form(),
                    Div(id="results"),
                    cls="container"
                )
            )
        )
    )


@rt("/search")
async def post(author: str = "", title: str = "", journal: str = ""):
    logger.info(
        f"Received search request: author={author}, title={title}, journal={journal}")

    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "author": author,
                "title": title,
                "journal": journal,
                "max_results": 100  # Request maximum results to populate cache
            }
            response = await client.post(f"{API_URL}/arxiv", json=payload)
            response.raise_for_status()
            logger.info(f"arXiv query response: {response.status_code}")

            results_response = await client.get(f"{API_URL}/results?page=0&items_per_page=10")
            results_response.raise_for_status()
            results = results_response.json()
            logger.info(f"Fetched {len(results['items'])} results out of {results['total']}")

            return results_list(results)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            return P(f"Error: {e.response.status_code} - {e.response.text}", cls="error-message")
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {e}")
            return P(f"Error: Unable to connect to the API. Please check if the backend is running.",
                     cls="error-message")


@rt("/search")
async def get(page: int = 1):
    async with httpx.AsyncClient() as client:
        try:
            results_response = await client.get(f"{API_URL}/results?page={page - 1}&items_per_page=10")
            results_response.raise_for_status()
            results = results_response.json()
            logger.info(f"Fetched {len(results['items'])} results for page {page}")
            return results_list(results, page)
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            return P(f"Error: {e.response.status_code} - {e.response.text}", cls="error-message")
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {e}")
            return P(f"Error: Unable to connect to the API. Please check if the backend is running.",
                     cls="error-message")


if __name__ == "__main__":
    serve(host=os.getenv("FRONTEND_HOST", "0.0.0.0"), port=int(os.getenv("FRONTEND_PORT", "5001")))
