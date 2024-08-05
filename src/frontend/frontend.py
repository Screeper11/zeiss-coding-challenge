import logging
from datetime import datetime, timezone, timedelta

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
            Label("Max Results", Input(type="number", name="max_results", value="8", min="1", max="50")),
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
        hx_include="[name='author'],[name='title'],[name='journal'],[name='max_results']"
    )


def results_list(results):
    if not results:
        return P("No results found.")

    return Ul(*[
        Li(
            H3(result['title']),
            P(f"Author: {result['author']}"),
            P(f"Journal: {result['journal']}")
        ) for result in results
    ])


@rt("/")
async def get():
    return Html(
        Head(
            Title("ZEISS Coding Challenge | Bence Papp"),
            Link(rel="stylesheet", href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css"),
            # Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap"),
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


@rt("/search", methods=["POST"])
async def post(author: str = "", title: str = "", journal: str = "", max_results: int = 8):
    logger.info(
        f"Received search request: author={author}, title={title}, journal={journal}, max_results={max_results}")

    async with httpx.AsyncClient() as client:
        try:
            payload = {
                "author": author,
                "title": title,
                "journal": journal,
                "max_results": max_results
            }
            response = await client.post(f"{API_URL}/arxiv", json=payload)
            response.raise_for_status()
            logger.info(f"arXiv query response: {response.status_code}")

            results_response = await client.get(f"{API_URL}/results")
            results_response.raise_for_status()
            results = results_response.json()
            logger.info(f"Fetched {len(results)} results")

            return results_list(results)

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            return P(f"Error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {e}")
            return P(f"Error: Unable to connect to the API. Please check if the backend is running.")


@rt("/queries")
async def get_queries():
    logger.info("Received request to fetch queries")

    async with httpx.AsyncClient() as client:
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=1)

            response = await client.get(f"{API_URL}/queries", params={
                "query_start_time": start_time.isoformat(),
                "query_end_time": end_time.isoformat()
            })
            response.raise_for_status()
            queries = response.json()
            logger.info(f"Fetched {len(queries)} queries")

            return Ul(*[
                Li(f"Query: {q['query']}, Timestamp: {q['timestamp']}, Status: {q['status']}, Results: {q['num_results']}")
                for q in queries
            ])

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            return P(f"Error: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            logger.error(f"Request error occurred: {e}")
            return P(f"Error: Unable to connect to the API. Please check if the backend is running.")


if __name__ == "__main__":
    serve(host=os.getenv("FRONTEND_HOST", "0.0.0.0"), port=int(os.getenv("FRONTEND_PORT", "5001")))
