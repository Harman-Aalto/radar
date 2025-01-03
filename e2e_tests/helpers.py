# Imports
from playwright.sync_api import Page

# Function to login
def login(page: Page) -> None:
    page.goto('http://localhost:8000/')
    page.get_by_label('Username').click()
    page.get_by_label('Username').fill('Username')
    page.get_by_label('Password').click()
    page.get_by_label('Password').fill('Password')
    page.get_by_role('link', name='Hide »').click()
    page.get_by_role('button', name='Login').click()
    page.get_by_role('link', name='Testcourse (testcourse)').click()

# Function to save settings and navigate back
def save_and_navigate_back(page: Page) -> None:
    page.locator('button[name=\'save\']').click()
    page.get_by_role('link', name='Testcourse').click()
