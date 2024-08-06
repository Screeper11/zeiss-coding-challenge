import logging

import httpx
from dotenv import load_dotenv
from fasthtml.common import *

from components import query_form, results_list

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)
load_dotenv()

app, rt = fast_app()

Favicon("assets/favicon.ico", "assets/favicon.ico")

BACKEND_API_BASE = os.getenv("BACKEND_API_URL_BASE", "http://api")
BACKEND_API_PORT = os.getenv("BACKEND_API_PORT", "8000")
API_URL = f"{BACKEND_API_BASE}:{BACKEND_API_PORT}"


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
    logger.info(f"Received search request: author={author}, title={title}, journal={journal}")

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


try:
    with open("assets/styles.css", 'r') as file:
        styles_css = file.read()
except (FileNotFoundError, IOError) as e:
    logger.error(f"Error reading CSS file: {e}")
    styles_css = ""

if __name__ == "__main__":
    serve(host=os.getenv("FRONTEND_HOST", "0.0.0.0"), port=int(os.getenv("FRONTEND_PORT", "5001")))
