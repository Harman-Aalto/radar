# Imports
import re
from playwright.sync_api import Page, expect
from random import randrange
from e2e_tests.helpers import login, save_and_navigate_back

# Test login
def test_login(page: Page) -> None:
    login(page)
    expect(page.get_by_role('navigation')).to_contain_text('Username@email.com Logout')

# Test logout
def test_logout(page: Page) -> None:
    login(page)
    page.get_by_role('button', name='Logout').click()
    expect(page.get_by_text('Password')).to_be_visible()

# Test change exercise name
def test_change_exercise_name(page: Page) -> None:
    exercise_num = randrange(9) + 1
    login(page)
    page.get_by_role('link', name=' Settings').click()
    page.get_by_label('Name').click()
    page.get_by_label('Name').fill(f'exercise{exercise_num}')
    save_and_navigate_back(page)
    expect(page.locator('tbody')).to_contain_text(f'exercise{exercise_num}')

# Test change exercise tokenizer
def test_change_tokenizer(page: Page) -> None:
    tokenizer = 'Python'
    change_to_tokenizer = 'Scala'

    if tokenizer == change_to_tokenizer:
        raise ValueError('Tokenizers are same')

    login(page)
    expect(page.locator('tbody')).to_contain_text(tokenizer)
    page.get_by_role('link', name=' Settings').click()
    page.get_by_label('Tokenizer type').select_option(change_to_tokenizer.lower())
    save_and_navigate_back(page)
    expect(page.locator('tbody')).to_contain_text(change_to_tokenizer)
    page.get_by_role('link', name=' Settings').click()
    page.get_by_label('Tokenizer type').select_option(tokenizer.lower())
    save_and_navigate_back(page)
    expect(page.locator('tbody')).to_contain_text(tokenizer)

# Test change exercise minimum match tokens
def test_change_minimum_match_tokens(page: Page) -> None:
    min_tokens = randrange(8) + 3
    login(page)
    page.get_by_role('link', name=' Settings').click()
    page.get_by_label('Minimum match tokens').click()
    page.get_by_label('Minimum match tokens').fill(f'{min_tokens}')
    save_and_navigate_back(page)
    expect(page.locator('tbody')).to_contain_text(f'{min_tokens} tokens')

# Test visibility of histogram and grid
def test_similarity_visibility(page: Page) -> None:
    login(page)
    page.get_by_role('link', name=re.compile(r'exercise.+')).click()
    expect(page.get_by_role('img')).to_contain_text(re.compile(r'.+0.00.10.20.30.40.50.60.70.80.91.0'))
    expect(page.locator('.comparison-grid')).to_be_visible()

# Test visibility of exercise histogram
def test_histogram_visibility(page: Page) -> None:
    login(page)
    page.get_by_role('link', name=' Exercise histograms').click()
    expect(page.get_by_role('img')).to_contain_text(re.compile(r'.+0.00.10.20.30.40.50.60.70.80.91.0'))

# Test visibility of student view
def test_student_view(page: Page) -> None:
    login(page)
    page.get_by_role('link', name=' Students view').click()
    page.get_by_role('link', name='1', exact=True).click()
    expect(page.locator('body')).to_contain_text(re.compile(r'exercise.+'))

# Test visibility of flagged pairs
def test_flagged_pairs(page: Page) -> None:
    login(page)
    page.get_by_role('link', name=re.compile(r'exercise.+')).click()
    page.get_by_role('link', name=re.compile(r'.+% .+ vs .+')).first.click()
    page.locator('[name="review"]').click()
    page.get_by_role('link', name='Plagiate', exact=True).click()
    page.get_by_role('link', name='Testcourse').click()
    page.get_by_role('link', name=' Flagged pairs').click()
    page.get_by_role('link', name=re.compile(r'.+ vs .+')).click()
    page.get_by_role('link', name='Get summary of marked').click()
    expect(page.get_by_role('heading')).to_contain_text('Similarity Summary')
