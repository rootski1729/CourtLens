import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper_exact_working import DelhiHighCourtScraper

class TestCourtLensScraper(unittest.TestCase):
    """Unit tests for CourtLens scraper functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scraper = DelhiHighCourtScraper()
    
    def test_scraper_initialization(self):
        """Test scraper initializes correctly"""
        self.assertIsNotNone(self.scraper)
        self.assertEqual(self.scraper.base_url, "https://delhihighcourt.nic.in")
        self.assertIn("W.P.(C)", self.scraper.case_types)
    
    def test_case_types_available(self):
        """Test case types are properly loaded"""
        case_types = self.scraper.get_case_types()
        self.assertIsInstance(case_types, dict)
        self.assertIn("W.P.(C)", case_types.values())
        self.assertIn("CRL.A.", case_types.values())
    
    def test_years_available(self):
        """Test years are properly loaded"""
        years = self.scraper.get_years()
        self.assertIsInstance(years, dict)
        self.assertIn("2019", years)
        self.assertIn("2020", years)
    
    def test_session_data_structure(self):
        """Test session data returns proper structure"""
        randomid, csrf_token = self.scraper.get_session_data()
        # Note: This might fail in CI without internet access
        if randomid and csrf_token:
            self.assertIsInstance(randomid, str)
            self.assertIsInstance(csrf_token, str)
            self.assertGreater(len(csrf_token), 10)  # CSRF tokens are long
    
    def test_search_result_structure(self):
        """Test search result has proper structure"""
        # Test with a known case (might fail if court site is down)
        result = self.scraper.search_case("W.P.(C)", "7608", "2019")
        
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('cases', result)
        
        if result['success'] and result['cases']:
            case = result['cases'][0]
            # Verify required fields exist
            required_fields = [
                'case_number', 'case_type', 'petitioner', 'respondent',
                'next_hearing_date', 'status'
            ]
            for field in required_fields:
                self.assertIn(field, case)

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
