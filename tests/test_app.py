import pytest
import json
from unittest.mock import patch, Mock

def test_index_route(client):
    """Test the main dashboard route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'CourtLens' in response.data
    assert b'Delhi High Court' in response.data

def test_search_case_get(client):
    """Test the search form GET request."""
    response = client.get('/search')
    assert response.status_code == 200
    assert b'Search Delhi High Court Cases' in response.data
    assert b'case_type' in response.data
    assert b'case_number' in response.data
    assert b'case_year' in response.data

def test_search_case_post_missing_data(client):
    """Test search form POST with missing required data."""
    response = client.post('/search', data={
        'case_type': '',
        'case_number': '',
        'case_year': ''
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'All fields are required' in response.data

@patch('app.scraper.search_case')
def test_search_case_post_success(mock_search, client):
    """Test successful case search."""
    # Mock successful search result
    mock_search.return_value = {
        'success': True,
        'cases': [
            {
                'diary_number': '123',
                'case_number': 'ABC/2024',
                'parties': 'John Doe vs State',
                'listing_date': '2024-01-15',
                'court_number': 'Court 1',
                'pdf_links': []
            }
        ]
    }
    
    response = client.post('/search', data={
        'case_type': 'civil',
        'case_number': '123',
        'case_year': '2024'
    })
    
    assert response.status_code == 200
    assert b'Found 1 case(s)' in response.data
    assert b'John Doe vs State' in response.data

@patch('app.scraper.search_case')
def test_search_case_post_error(mock_search, client):
    """Test case search with error."""
    # Mock error result
    mock_search.return_value = {
        'error': 'CAPTCHA validation failed'
    }
    
    response = client.post('/search', data={
        'case_type': 'civil',
        'case_number': '123',
        'case_year': '2024'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'CAPTCHA validation failed' in response.data

@patch('app.scraper.get_case_types')
def test_api_case_types(mock_get_types, client):
    """Test the case types API endpoint."""
    mock_get_types.return_value = {
        'Civil': 'civil',
        'Criminal': 'criminal'
    }
    
    response = client.get('/api/case-types')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'case_types' in data
    assert data['case_types']['Civil'] == 'civil'

@patch('app.scraper.get_years')
def test_api_years(mock_get_years, client):
    """Test the years API endpoint."""
    mock_get_years.return_value = {
        '2024': '2024',
        '2023': '2023'
    }
    
    response = client.get('/api/years')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'years' in data

@patch('app.scraper._get_captcha_info')
def test_api_captcha(mock_get_captcha, client):
    """Test the CAPTCHA API endpoint."""
    mock_get_captcha.return_value = {
        'code': '1234',
        'image_url': 'http://example.com/captcha.png'
    }
    
    response = client.get('/api/captcha')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['success'] is True
    assert 'captcha' in data

def test_search_history_empty(client):
    """Test search history with no searches."""
    response = client.get('/history')
    assert response.status_code == 200
    assert b'No Search History' in response.data

def test_404_error(client):
    """Test 404 error page."""
    response = client.get('/nonexistent-page')
    assert response.status_code == 404
    assert b'Page not found' in response.data

def test_case_detail_not_found(client):
    """Test case detail page with non-existent case ID."""
    response = client.get('/case/999')
    assert response.status_code == 404
