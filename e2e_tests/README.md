# Radar Testing Guide

This document provides a guide to create and run end-to-end tests for Radar using [Playwright](https://playwright.dev/python/).

## Set up environment

Make sure everything is set up following this [Radar development guide](https://github.com/apluslms/radar/blob/master/doc/DEVELOPMENT.md) before continuing.

1. Run Python environment: `source py_venv/bin/activate`

2. Before testing create super user using: `python manage.py createsuperuser`<br>
    Username: `Username`<br>
    Email: `Username@email.com`<br>
    Password: `Password`<br>

3. Run server: `python manage.py runserver`

4. Load submissions: `./run_loadsubmissions.sh ${directory_with_submissions} testcourse exercise1 1`

5. Match submissions: `python manage.py matchsubmissions testcourse/exercise1`

## Create tests

1. Open new terminal.

2. Run Python environment: `source py_venv/bin/activate`

3. Record tests: `playwright codegen --target python-pytest "localhost:8000"`

4. Copy generated code into a Python file.

[Generating tests](https://playwright.dev/python/docs/codegen-intro)

[Writing tests](https://playwright.dev/python/docs/writing-tests)

## Run and debug tests

Run all tests: `pytest`

Run and debug a specific test: `PWDEBUG=1 pytest -s -k <test_method_name>`

[Running and debugging tests](https://playwright.dev/python/docs/running-tests)
