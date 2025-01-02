# Imports
import re
from playwright.sync_api import Page, expect

# Test to check Dolos working
def test_dolos(page: Page) -> None:
    page.goto("http://localhost:8000/")
    page.get_by_label("Username").click()
    page.get_by_label("Username").fill("Username")
    page.get_by_label("Password").click()
    page.get_by_label("Password").fill("Password")
    page.get_by_role("link", name="Hide »").click()
    page.get_by_role("button", name="Login").click()
    page.get_by_role("link", name="Testcourse (testcourse)").click()
    text = page.get_by_role("link", name=re.compile(r"exercise.+")).all_inner_texts()[0]
    page.get_by_role("link", name=text).click()
    page.locator("#dolos-filter").select_option("all")
    page.get_by_role("link", name="Run analysis").click()
    expect(page.get_by_text("Source code plagiarism")).to_be_visible(timeout=25000)
