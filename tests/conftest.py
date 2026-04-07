import pytest
import sys
import os
import sqlite3
from pathlib import Path

# Add parent directory to path so we can import llcScraper modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'llcScraper'))

# Use a test database
TEST_DB = Path('config/test_llcscraper.db')


@pytest.fixture(autouse=True)
def setup_test_db():
    """Set up a fresh test database for each test."""
    # Clean up old test db
    if TEST_DB.exists():
        TEST_DB.unlink()

    # Ensure config dir exists
    TEST_DB.parent.mkdir(exist_ok=True)

    # Override the DB_PATH in the database module
    import database
    original_db = database.DB_PATH
    database.DB_PATH = TEST_DB

    # Initialize the test database
    database.init_db()
    database.run_migrations()

    yield

    # Cleanup after test
    database.DB_PATH = original_db
    if TEST_DB.exists():
        TEST_DB.unlink()


@pytest.fixture
def app():
    """Create and configure a test Flask app."""
    import database

    # Use test database
    database.DB_PATH = TEST_DB

    # Import after setting DB_PATH
    from app import app as flask_app

    flask_app.config['TESTING'] = True

    return flask_app


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
