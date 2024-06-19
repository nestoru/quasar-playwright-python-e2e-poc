import pytest
import json
import os
import re
from playwright.sync_api import sync_playwright, expect
from datetime import datetime

# Load configuration from config.json
with open('config.json') as config_file:
    config = json.load(config_file)

log_file = config.get('E2E_LOG_FILE', '/tmp/e2e-log.txt')

# Function to log messages to a file
def log_to_file(message):
    with open(log_file, 'a') as f:
        f.write(f'{datetime.now().isoformat()} - {message}\n')

@pytest.fixture(scope="session", autouse=True)
def global_setup():
    with open('config.json') as config_file:
        cfg = json.load(config_file)
    
    os.environ['E2E_APP_URL'] = cfg['E2E_APP_URL']
    os.environ['E2E_USER'] = cfg['E2E_USER']
    os.environ['E2E_PASSWORD'] = cfg['E2E_PASSWORD']
    os.environ['E2E_UNIQUE_CONTEXT'] = cfg['E2E_UNIQUE_CONTEXT']

def create_user(page, email, first_name, last_name, role, user_password):
    log_to_file(f'Creating user: {email}')

    # Search for user
    log_to_file('Waiting for search bar to be visible')
    page.wait_for_selector('input.q-field__native[placeholder="Search"]', state='visible')
    page.fill('input.q-field__native[placeholder="Search"]', email)

    # Wait for the loading spinner to disappear
    log_to_file('Waiting for loading spinner to disappear')
    page.wait_for_selector('.blurred-form', state='hidden')

    # Assert that a form appears with "Email", "First Name", "Last Name", and "Password" input fields; a checkbox called "Use SSO"; and a multi select called "Roles"
    user_row = page.locator(f'tr:has-text("{email}")')
    if user_row.count() == 0:
        log_to_file('User not found, clicking Add button')
        page.click('button:has-text("Add")')
    else:
        log_to_file('User found, clicking Edit button')
        user_row.locator('button:has-text("Edit")').click()

    # Wait for the form to be unblurred before locating elements
    log_to_file('Waiting for form to unblur')
    page.wait_for_selector('.blurred-form', state='hidden')

    log_to_file('Verifying user form fields are visible')
    expect(page.locator('input[aria-label="Email"]')).to_be_visible()
    expect(page.locator('input[aria-label="First Name"]')).to_be_visible()
    expect(page.locator('input[aria-label="Last Name"]')).to_be_visible()
    password_input = page.locator('input[aria-label="Password"]')
    expect(password_input).to_be_visible()
    form_sso_checkbox = page.locator('.q-checkbox')
    expect(form_sso_checkbox).to_be_visible()
    expect(page.locator('.q-select')).to_be_visible()

    # Log the page content before interacting with the roles dropdown
    page_content = page.content()
    with open(log_file, 'a') as f:
        f.write(f'\nPage content before roles dropdown:\n{page_content}\n')

    # Complete the form with email, First Name, Last Name, unchecked "Use SSO", and Roles
    log_to_file('Filling user form fields')
    page.fill('input[aria-label="Email"]', email)
    page.fill('input[aria-label="First Name"]', first_name)
    page.fill('input[aria-label="Last Name"]', last_name)
    if form_sso_checkbox.get_attribute('aria-checked') == 'true':
        form_sso_checkbox.click()  # Ensure it is unchecked
    page.fill('input[aria-label="Password"]', user_password)  # Fill the password field since SSO is unchecked

    # Press tab to navigate to the roles dropdown and press enter to expand it
    log_to_file('Pressing Tab from Password field to navigate to roles dropdown')
    page.press('input[aria-label="Password"]', 'Tab')
    log_to_file('Pressing Enter to expand roles dropdown')
    page.press('input[role="combobox"][aria-label="Roles"]', 'Enter')

    # Log the page content after attempting to expand the dropdown
    page_content_after_click = page.content()
    with open(log_file, 'a') as f:
        f.write(f'\nPage content after roles dropdown expansion:\n{page_content_after_click}\n')

    # Ensure the role is selected
    log_to_file('Selecting role')
    role_input = page.locator('div.q-field__native span')
    selected_role = role_input.inner_text()
    if role not in selected_role:
        role_option = page.locator(f'div[role="option"]:has-text("{role}")')
        role_option.click()
        # Wait for the role to be added to the input field
        page.wait_for_function(
            'role => document.querySelector("div.q-field__native span").innerText.includes(role)',
            role,
            timeout=5000
        )

    # Ensure the dropdown is closed
    log_to_file('Ensuring dropdown is closed')
    page.click('body', force=True)

    # Wait for the "Save" button to be interactable and click it
    log_to_file('Clicking Save button')
    save_button = page.locator('button span.block:has-text("Save")')
    save_button.wait_for(state='visible')
    save_button.click()

def test_authentication_and_authorization():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(record_video_dir='test-results/videos', viewport={'width': 1280, 'height': 720})
        page = context.new_page()
        app_url = os.getenv('E2E_APP_URL')
        user_email = os.getenv('E2E_USER')
        user_password = os.getenv('E2E_PASSWORD')
        unique_context = os.getenv('E2E_UNIQUE_CONTEXT')

        if not app_url or not user_email or not user_password or not unique_context:
            raise ValueError('Missing required environment variables in config.json')

        log_to_file('Starting test - navigating to app URL')
        page.goto(app_url)

        # Wait for the page to be unblurred before locating elements
        page.wait_for_selector('.blurred-page', state='hidden')

        # Assert that Password and Email fields are visible and that the "Use SSO" checkbox is unchecked
        log_to_file('Checking visibility of Email and Password fields')
        expect(page.locator('input[aria-label="Email"]')).to_be_visible()
        expect(page.locator('input[aria-label="Password"]')).to_be_visible()
        sso_checkbox = page.locator('.q-checkbox')
        assert re.search(r'q-checkbox--checked', sso_checkbox.get_attribute('class')) is None

        # Click on "Login" button
        log_to_file('Clicking on Login button without filling fields')
        page.click('button:has-text("Login")')
        # Assert div with content "Password is required" shows up
        expect(page.locator('.text-negative:has-text("Password is required")')).to_be_visible()

        # Check "Use SSO" checkbox
        log_to_file('Checking Use SSO checkbox and verifying Password field hides')
        sso_checkbox.click()
        # Assert the Password input disappears
        expect(page.locator('input[aria-label="Password"]')).to_be_hidden()

        # Click on "Login" button
        log_to_file('Clicking on Login button with SSO checked')
        page.click('button:has-text("Login")')
        # Assert div with content "Invalid credentials or unsupported provider" shows up
        expect(page.locator('.text-negative:has-text("Invalid credentials or unsupported provider")')).to_be_visible()

        # Enter "anything@sample.com" in the email field
        log_to_file('Entering invalid email and clicking Login')
        page.fill('input[aria-label="Email"]', 'anything@sample.com')
        # Click on "Login" button
        page.click('button:has-text("Login")')
        # Assert div with content "Invalid credentials or unsupported provider" shows up
        expect(page.locator('.text-negative:has-text("Invalid credentials or unsupported provider")')).to_be_visible()

        # Enter mandatory E2E_USER env var in the Email field and mandatory E2E_PASSWORD env var in the Password field
        log_to_file('Entering valid email and password')
        page.fill('input[aria-label="Email"]', user_email)
        sso_checkbox.click()  # Uncheck the "Use SSO" checkbox
        page.fill('input[aria-label="Password"]', user_password)
        # Click on "Login" button
        page.click('button:has-text("Login")')

        # Click on the menu item "Users"
        log_to_file('Waiting for Users menu item and clicking it')
        page.wait_for_selector('div.q-item__section:has-text("Users")', state='visible')
        page.click('div.q-item__section:has-text("Users")')

        # Create users
        log_to_file('Creating first user')
        create_user(page, f'e2e+allreports+{unique_context}@sample.com', 'e2e', 'allreports', 'REPORT_READ_ALL', user_password)
        log_to_file('Creating second user')
        create_user(page, f'e2e+physician_all_fields+{unique_context}@sample.com', 'e2e', 'physician_all_fields', 'REPORT_READ_PHYSICIAN-ALL-FIELDS', user_password)

        # Click "Logoff" button
        log_to_file('Logging off')
        page.wait_for_selector('div.q-item__section:has-text("Logoff")', state='visible')
        page.click('div.q-item__section:has-text("Logoff")')

        # Enter email e2e+physician_all_fields+{E2E_UNIQUE_CONTEXT}@sample.com, password={E2E_PASSWORD}
        log_to_file('Logging in as the second user')
        page.fill('input[aria-label="Email"]', f'e2e+physician_all_fields+{unique_context}@sample.com')
        page.fill('input[aria-label="Password"]', user_password)
        # Click "Login" button
        page.click('button:has-text("Login")')
        # Assert that menu items "Reports" and "Profile" are visible but "Users" is not
        expect(page.locator('div.q-item__section:has-text("Reports")')).to_be_visible()
        expect(page.locator('div.q-item__section:has-text("Profile")')).to_be_visible()
        expect(page.locator('div.q-item__section:has-text("Users")')).to_be_hidden()

        # Click on the "Reports" menu item
        log_to_file('Navigating to Reports')
        page.click('div.q-item__section:has-text("Reports")')
        # Assert that a list of reports show up with just one row containing physician_all_fields as content
        page.wait_for_selector('.blurred-form', state='hidden')
        expect(page.locator('td:has-text("physician_all_fields")')).to_be_visible()

        # Click on "Profile" menu item
        log_to_file('Navigating to Profile')
        page.click('div.q-item__section:has-text("Profile")')
        
        # Wait for the loading spinner to disappear
        log_to_file('Waiting for profile loading spinner to disappear')
        page.wait_for_selector('.blurred-form', state='hidden')

        # Assert the field labeled "Email" is read only
        expect(page.locator('input[aria-label="Email"]')).to_have_attribute('readonly', '')

        # Type "e2e physician_all_fields" in the field labeled "First Name"
        log_to_file('Updating Profile information')
        page.fill('input[aria-label="First Name"]', 'e2e physician_all_fields')
        # Collect current date to the seconds as saved_at
        saved_at = datetime.now().isoformat()
        # Type the value of saved_at in the field labeled "Last Name"
        page.fill('input[aria-label="Last Name"]', saved_at)

        # Click on the plus sign of the file upload widget and pick the file e2e.png
        log_to_file('Uploading file')
        page.set_input_files('input[type="file"]', 'resources/e2e.png')
        # Click the "Save" button
        page.click('button:has-text("Save")')
        # Wait for the loading spinner to disappear
        page.wait_for_selector('.blurred-form', state='hidden')

        # Refresh the page
        log_to_file('Refreshing page')
        page.reload()

        # Wait for the loading spinner to disappear
        page.wait_for_selector('.blurred-form', state='hidden')

        # Assert that "Last Name" is the value of saved_at
        expect(page.locator('input[aria-label="Last Name"]')).to_have_value(saved_at)

        # Logoff
        log_to_file('Logging off to end the test')
        page.click('div.q-item__section:has-text("Logoff")')

        context.close()
        browser.close()

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_call(item):
    # Capture screenshot and video on failure
    outcome = yield
    rep = outcome.get_result()
    if rep.failed:
        page = item.funcargs['page']
        screenshot_path = f"test-results/screenshots/{item.name}.png"
        video_path = page.video.path()
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        print(f"Video saved to {video_path}")

