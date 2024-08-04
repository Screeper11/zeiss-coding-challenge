from fasthtml.common import *
import httpx
import logging
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app, rt = fast_app()

API_URL = "http://api:8000"


def query_form():
    return Form(
        H2("arXiv Query Parameters"),
        Label("Author:", Input(type="text", name="author")),
        Label("Title:", Input(type="text", name="title")),
        Label("Journal:", Input(type="text", name="journal")),
        Label("Max Results:", Input(type="number", name="max_results", value="8")),
        Button("Search", type="submit"),
        id="search-form",
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
            f"Author: {result['author']}, ",
            f"Title: {result['title']}, ",
            f"Journal: {result['journal']}"
        ) for result in results
    ])


@rt("/")
async def get():
    return Html(
        Head(
            Title("arXiv Query Frontend"),
            Link(rel="stylesheet", href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css"),
            Script(src="https://unpkg.com/htmx.org@1.9.10")
        ),
        Body(
            Main(
                H1("arXiv Query Frontend"),
                query_form(),
                Div(id="results")
            )
        )
    )


@rt("/search", methods=["POST"])
async def post(author: str = "", title: str = "", journal: str = "", max_results: int = 8):
    logger.info(
        f"Received search request: author={author}, title={title}, journal={journal}, max_results={max_results}")

    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Query arXiv
            response = await client.post(f"{API_URL}/arxiv", json={
                "author": author,
                "title": title,
                "journal": journal,
                "max_results": max_results
            })
            response.raise_for_status()
            logger.info(f"arXiv query response: {response.status_code}")

            # Step 2: Fetch results
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
            # Use the current time as the end time and 24 hours ago as the start time
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
    serve()
