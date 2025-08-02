import pytest
import os
import sys
import tempfile

# Add the parent directory to the path so we can import our app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db

@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    # Create a temporary file for the test database
    db_fd, app.config['DATABASE_URL'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
    
    os.close(db_fd)
    os.unlink(app.config['DATABASE_URL'])

@pytest.fixture
def app_context():
    """Create an application context for testing."""
    with app.app_context():
        yield app
