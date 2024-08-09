import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(scope="function", autouse=True)
def before_each_after_each(page: Page):
    page.goto("http://localhost:5001")
    yield


def test_home_page_loads(page: Page):
    expect(page.locator("h1")).to_contain_text("ZEISS Coding Challenge")
    expect(page.locator("#search-form")).to_be_visible()


def test_search_form_submission(page: Page):
    page.fill('input[name="author"]', "Einstein")
    page.click('button[type="submit"]')
    expect(page.locator("#results")).to_be_visible()
    count = page.locator("#results li").count()
    assert count > 0


def test_pagination(page: Page):
    page.fill('input[name="author"]', "Einstein")
    page.click('button[type="submit"]')
    expect(page.locator(".pagination")).to_be_visible()
    page.click('.pagination a:nth-child(2)')  # Click on page 2
    count = page.locator("#results li").count()
    assert count > 0


def test_search_button_disabled_on_empty_input(page: Page):
    # Clear all input fields
    page.fill('input[name="author"]', "")
    page.fill('input[name="title"]', "")
    page.fill('input[name="journal"]', "")

    # Check if the search button is disabled
    expect(page.locator('button[type="submit"]')).to_be_disabled()


def test_result_display(page: Page):
    page.fill('input[name="author"]', "Einstein")
    page.click('button[type="submit"]')

    # Check if the results container is visible
    expect(page.locator("#results")).to_be_visible()

    count = page.locator("#results li").count()

    assert count > 0

    # Check additional elements if results are present
    if count > 0:
        expect(page.locator("#results li h3").first).to_be_visible()  # Check if at least one title is visible
        expect(page.locator("#results li p").first).to_contain_text("Author:")
        # Adjust the test based on actual content
        expect(page.locator("#results li p").first).not_to_contain_text("Journal:")
        # Alternatively, if Journal should be present and it's not:
        expect(page.locator("#results li p").nth(1)).to_contain_text("Journal:")


def test_form_submission_values(page: Page):
    page.fill('input[name="author"]', "Einstein")
    page.fill('input[name="title"]', "Relativity")
    page.fill('input[name="journal"]', "Physics")
    page.click('button[type="submit"]')
    # Check if the form values are still present after submission
    expect(page.locator('input[name="author"]')).to_have_value("Einstein")
    expect(page.locator('input[name="title"]')).to_have_value("Relativity")
    expect(page.locator('input[name="journal"]')).to_have_value("Physics")


if __name__ == "__main__":
    pytest.main([__file__])
