import pytest
import sys
import os
import tempfile
from playwright.sync_api import sync_playwright

# Create temp directory BEFORE any backend imports
_temp_dir = tempfile.mkdtemp(prefix='fauxx_test_')
os.environ['DATA_DIR'] = _temp_dir

# Add backend to path
sys.path.insert(0, '/home/steimer/fauxx-docker/backend')

# Base URL for tests
BASE_URL = "http://localhost:8000"

# API Key for tests
API_KEY = "a247c8d858733a9cde76c2974d4e02ef0c4bcde4232da8145ddf76862f827293"


@pytest.fixture
def page():
    """Create a Playwright page for testing."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        yield page
        page.close()
        context.close()
        browser.close()


@pytest.fixture(autouse=True)
def reset_settings_singleton():
    """Reset SettingsManager singleton before each test."""
    from app.settings import SettingsManager
    SettingsManager._instance = None
    yield
    SettingsManager._instance = None
