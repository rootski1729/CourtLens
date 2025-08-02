import pytest
from unittest.mock import Mock, patch
from scraper import DelhiHighCourtScraper

class TestDelhiHighCourtScraper:
    """Test cases for the Delhi High Court scraper."""
    
    def test_init(self):
        """Test scraper initialization."""
        scraper = DelhiHighCourtScraper()
        
        assert scraper.base_url == "https://delhihighcourt.nic.in"
        assert scraper.search_url == "https://delhihighcourt.nic.in/app/get-case-type-status"
        assert scraper.session is not None
    
    def test_init_with_config(self):
        """Test scraper initialization with custom config."""
        config = {
            'tesseract_path': '/custom/path/tesseract',
            'save_raw': True
        }
        scraper = DelhiHighCourtScraper(config)
        
        assert scraper.config == config
    
    @patch('scraper.requests.Session.get')
    def test_get_csrf_token_success(self, mock_get):
        """Test successful CSRF token extraction."""
        # Mock response with CSRF token in script
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'''
        <html>
            <script>
                var config = {"_token": "test-csrf-token-12345"};
            </script>
        </html>
        '''
        mock_get.return_value = mock_response
        
        scraper = DelhiHighCourtScraper()
        token = scraper._get_csrf_token()
        
        assert token == "test-csrf-token-12345"
        assert scraper.csrf_token == "test-csrf-token-12345"
    
    @patch('scraper.requests.Session.get')
    def test_get_csrf_token_not_found(self, mock_get):
        """Test CSRF token extraction when token is not found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'<html><body>No token here</body></html>'
        mock_get.return_value = mock_response
        
        scraper = DelhiHighCourtScraper()
        token = scraper._get_csrf_token()
        
        assert token is None
    
    @patch('scraper.pytesseract.image_to_string')
    @patch('scraper.requests.Session.get')
    def test_get_captcha_info_with_ocr(self, mock_get, mock_ocr):
        """Test CAPTCHA extraction with OCR."""
        # Mock main page response
        mock_main_response = Mock()
        mock_main_response.content = b'''
        <html>
            <input name="randomid" value="1234">
        </html>
        '''
        
        # Mock CAPTCHA image response
        mock_captcha_response = Mock()
        mock_captcha_response.status_code = 200
        mock_captcha_response.content = b'fake-image-data'
        
        mock_get.side_effect = [mock_main_response, mock_captcha_response]
        mock_ocr.return_value = '5678'
        
        scraper = DelhiHighCourtScraper()
        captcha_info = scraper._get_captcha_info()
        
        assert captcha_info is not None
        assert captcha_info['code'] == '1234'  # From randomid field
    
    @patch('scraper.requests.Session.post')
    def test_validate_captcha_success(self, mock_post):
        """Test successful CAPTCHA validation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True}
        mock_post.return_value = mock_response
        
        scraper = DelhiHighCourtScraper()
        scraper.csrf_token = 'test-token'
        
        result = scraper._validate_captcha('1234')
        
        assert result is True
    
    @patch('scraper.requests.Session.post')
    def test_validate_captcha_failure(self, mock_post):
        """Test failed CAPTCHA validation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': False}
        mock_post.return_value = mock_response
        
        scraper = DelhiHighCourtScraper()
        scraper.csrf_token = 'test-token'
        
        result = scraper._validate_captcha('wrong-captcha')
        
        assert result is False
    
    def test_parse_html_response_with_data(self):
        """Test HTML response parsing with case data."""
        html_content = '''
        <html>
            <table>
                <tr><th>Diary No</th><th>Case No</th><th>Parties</th></tr>
                <tr>
                    <td>123</td>
                    <td>ABC/2024</td>
                    <td>John Doe vs State</td>
                    <td>2024-01-15</td>
                    <td>Court 1</td>
                </tr>
            </table>
        </html>
        '''
        
        scraper = DelhiHighCourtScraper()
        result = scraper._parse_html_response(html_content)
        
        assert result['success'] is True
        assert len(result['cases']) == 1
        assert result['cases'][0]['diary_number'] == '123'
        assert result['cases'][0]['case_number'] == 'ABC/2024'
        assert result['cases'][0]['parties'] == 'John Doe vs State'
    
    def test_parse_html_response_no_table(self):
        """Test HTML response parsing with no table."""
        html_content = '<html><body>No table here</body></html>'
        
        scraper = DelhiHighCourtScraper()
        result = scraper._parse_html_response(html_content)
        
        assert 'error' in result
        assert 'No case data found' in result['error']
    
    def test_parse_json_response_success(self):
        """Test JSON response parsing with success."""
        json_data = {
            'success': True,
            'data': [
                {'case_number': '123/2024', 'parties': 'Test vs Test'}
            ]
        }
        
        scraper = DelhiHighCourtScraper()
        result = scraper._parse_json_response(json_data)
        
        assert result['success'] is True
        assert len(result['cases']) == 1
    
    def test_parse_json_response_error(self):
        """Test JSON response parsing with error."""
        json_data = {
            'success': False,
            'message': 'Invalid case number'
        }
        
        scraper = DelhiHighCourtScraper()
        result = scraper._parse_json_response(json_data)
        
        assert 'error' in result
        assert result['error'] == 'Invalid case number'
    
    @patch('scraper.DelhiHighCourtScraper._get_captcha_info')
    @patch('scraper.DelhiHighCourtScraper._validate_captcha')
    @patch('scraper.DelhiHighCourtScraper._get_csrf_token')
    @patch('scraper.requests.Session.post')
    def test_search_case_success(self, mock_post, mock_csrf, mock_validate, mock_captcha):
        """Test successful case search."""
        # Setup mocks
        mock_csrf.return_value = 'test-token'
        mock_captcha.return_value = {'code': '1234'}
        mock_validate.return_value = True
        
        mock_response = Mock()
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.content = '''
        <table>
            <tr><th>Case</th></tr>
            <tr><td>Test Case</td></tr>
        </table>
        '''
        mock_post.return_value = mock_response
        
        scraper = DelhiHighCourtScraper()
        result = scraper.search_case('civil', '123', '2024')
        
        assert result['success'] is True
    
    def test_get_case_types_returns_dict(self):
        """Test that get_case_types returns a dictionary."""
        scraper = DelhiHighCourtScraper()
        case_types = scraper.get_case_types()
        
        assert isinstance(case_types, dict)
    
    def test_get_years_returns_dict(self):
        """Test that get_years returns a dictionary."""
        scraper = DelhiHighCourtScraper()
        years = scraper.get_years()
        
        assert isinstance(years, dict)
