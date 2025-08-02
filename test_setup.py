#!/usr/bin/env python3
"""
CourtLens - Test Runner
Quick test to verify all components are working
"""

import os
import sys
import sqlite3
from dotenv import load_dotenv

def test_environment():
    """Test environment setup"""
    print("🧪 Testing Environment Setup...")
    
    # Load environment variables
    load_dotenv()
    
    print(f"✅ Python version: {sys.version}")
    print(f"✅ Working directory: {os.getcwd()}")
    print(f"✅ Environment loaded: {os.getenv('SECRET_KEY') is not None}")
    
def test_database():
    """Test database creation"""
    print("\n🗄️ Testing Database Setup...")
    
    try:
        conn = sqlite3.connect('courtlens.db')
        cursor = conn.cursor()
        
        # Create test table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY,
                name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert test data
        cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("test_record",))
        
        # Query test data
        cursor.execute("SELECT * FROM test_table")
        result = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        print(f"✅ Database created and tested successfully")
        print(f"✅ Test record: {result}")
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    return True

def test_imports():
    """Test required imports"""
    print("\n📦 Testing Package Imports...")
    
    try:
        import flask
        print(f"✅ Flask {flask.__version__}")
        
        import requests
        print(f"✅ Requests {requests.__version__}")
        
        import bs4
        print(f"✅ BeautifulSoup {bs4.__version__}")
        
        from selenium import webdriver
        print(f"✅ Selenium imported")
        
        import pytesseract
        print(f"✅ PyTesseract imported")
        
        from PIL import Image
        print(f"✅ Pillow imported")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_scraper():
    """Test scraper initialization"""
    print("\n🕷️ Testing Scraper...")
    
    try:
        sys.path.append(os.getcwd())
        from scraper import DelhiHighCourtScraper
        
        # Initialize scraper
        scraper = DelhiHighCourtScraper({'tesseract_path': 'tesseract'})
        print(f"✅ Scraper initialized")
        print(f"✅ Base URL: {scraper.base_url}")
        
        # Test basic methods
        case_types = scraper.get_case_types()
        print(f"✅ Case types loaded: {len(case_types)} types")
        
        years = scraper.get_years()  
        print(f"✅ Years loaded: {len(years)} years")
        
        return True
        
    except Exception as e:
        print(f"❌ Scraper error: {e}")
        return False

def test_flask_app():
    """Test Flask app initialization"""
    print("\n🌐 Testing Flask Application...")
    
    try:
        sys.path.append(os.getcwd())
        from app_simple import app
        
        # Test app configuration
        print(f"✅ Flask app created")
        print(f"✅ Secret key configured: {bool(app.config.get('SECRET_KEY'))}")
        
        # Test routes exist
        with app.test_client() as client:
            response = client.get('/')
            print(f"✅ Index route responds: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask app error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 CourtLens - Comprehensive Test Suite")
    print("=" * 50)
    
    tests = [
        test_environment,
        test_imports,
        test_database,
        test_scraper,
        test_flask_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! CourtLens is ready to run.")
        print("\n📋 Next steps:")
        print("1. Run: python app_simple.py")
        print("2. Open: http://localhost:5000")
        print("3. Test the Delhi High Court scraper!")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
