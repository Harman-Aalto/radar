# Imports
import re
from playwright.sync_api import Page, expect
from e2e_tests.helpers import login

# Test to check if Dolos is generating the plagiarism report
def test_dolos(page: Page) -> None:
    login(page)
    page.get_by_role('link', name=re.compile(r'exercise.+')).click()
    page.locator('#dolos-filter').select_option('all')
    page.get_by_role('link', name='Run analysis').click()
    expect(page.get_by_text('Source code plagiarism')).to_be_visible(timeout=25000)
