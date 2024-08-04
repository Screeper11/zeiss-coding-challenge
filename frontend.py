from fasthtml.common import *
import httpx

app, rt = fast_app()

API_URL = "http://api:8000"  # Use the service name defined in docker-compose.yml

def query_form():
    return Form(
        H2("arXiv Query Parameters"),
        Label("Author:", Input(type="text", name="author")),
        Label("Title:", Input(type="text", name="title")),
        Label("Journal:", Input(type="text", name="journal")),
        Label("Max Results:", Input(type="number", name="max_results", value="8")),
        Button("Search", type="submit"),
        hx_post="/search",
        hx_target="#results"
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
            Link(rel="stylesheet", href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css")
        ),
        Body(
            Main(
                H1("arXiv Query Frontend"),
                query_form(),
                Div(id="results")
            )
        )
    )

@rt("/search")
async def post(author: str = "", title: str = "", journal: str = "", max_results: int = 8):
    params = {
        "author": author,
        "title": title,
        "journal": journal,
        "max_results": max_results
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_URL}/arxiv", params=params)

    if response.status_code == 200:
        # For demonstration purposes, we'll fetch and display the results immediately
        # In a real-world scenario, you might want to separate this into another API call
        results_response = await client.get(f"{API_URL}/results")
        if results_response.status_code == 200:
            results = results_response.json()
            return results_list(results)
        else:
            return P(f"Error fetching results: {results_response.status_code} - {results_response.text}")
    else:
        return P(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    serve()
