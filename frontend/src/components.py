from fasthtml.common import *


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
        Button("Search", type="submit", id="search-button", disabled="true"),
        id="search-form",
        cls="search-form",
        hx_post="/search",
        hx_target="#results",
        hx_swap="innerHTML",
        hx_include="[name='author'],[name='title'],[name='journal']",
        hx_on="input: checkInputs()"
    )


def checkInputs():
    return Script("""
    function checkInputs() {
        var inputs = document.querySelectorAll('#search-form input[type="text"]');
        var button = document.querySelector('#search-button');
        var isEmpty = Array.from(inputs).every(input => input.value.trim() === '');
        button.disabled = isEmpty;
    }
    """)


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
