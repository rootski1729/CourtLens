# CourtLens - Delhi High Court Case Search System

## Overview
CourtLens is a web application that fetches case information from the Delhi High Court website. It provides a clean interface for searching cases and viewing results with proper session management and security handling.

## Features
- **Case Search**: Search by case type, number, and year
- **CSRF Protection**: Automatic token extraction and validation
- **Session Management**: Proper cookie and session handling
- **Case Details**: Complete case information including parties, advocates, and hearing dates
- **Search History**: Track all searches with timestamps and results
- **Error Handling**: User-friendly error messages and validation
- **Rate Limiting**: API protection against excessive requests

## Tech Stack
- **Backend**: Python Flask 3.0
- **Database**: SQLite
- **Web Scraping**: Requests + BeautifulSoup
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **Security**: Flask-Limiter for rate limiting

## Quick Start

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd CourtLens

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python setup_db.py

# Run the application
python app_simple.py
```

## Project Structure
```
CourtLens/
├── app_simple.py          # Main Flask application
├── scraper_fast.py        # Delhi High Court scraper
├── setup_db.py           # Database initialization
├── requirements.txt       # Python dependencies
├── courtlens.db          # SQLite database
├── templates/            # HTML templates
├── static/              # CSS, JS, images
├── tests/               # Test files
└── README.md            # Project documentation
```
# Linux: sudo apt-get install tesseract-ocr
# Mac: brew install tesseract
```

### Installation
```bash
# Clone repository
git clone https://github.com/rootski1729/CourtLens.git
cd CourtLens

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Environment Variables
```bash
# .env file
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///courtlens.db
TESSERACT_PATH=/usr/bin/tesseract  # Adjust path as needed
RATE_LIMIT_PER_HOUR=60
LOG_LEVEL=INFO
```

### Running the Application
```bash
# Initialize database
python app.py init-db

# Run development server
python app.py

# Access at http://localhost:5000
```

## Usage
1. **Start the application**: `python app_simple.py`
2. **Open browser**: Navigate to `http://localhost:5000`
3. **Search cases**: Enter case type, number, and year
4. **View results**: See complete case details and history
5. **Check history**: View all previous searches

## API Endpoints
- `GET /` - Main dashboard
- `GET /search` - Search form
- `POST /search` - Process search request
- `GET /history` - View search history
- `GET /api/case-types` - Get available case types
- `GET /api/years` - Get available years

## Database Schema
```sql
CREATE TABLE cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_number TEXT NOT NULL,
    case_type TEXT NOT NULL,
    status TEXT,
    petitioner TEXT,
    respondent TEXT,
    petitioner_advocate TEXT,
    respondent_advocate TEXT,
    next_hearing_date TEXT,
    court_number TEXT,
    raw_data TEXT
);

CREATE TABLE search_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_params TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    results_count INTEGER DEFAULT 0,
    error_message TEXT,
    ip_address TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Docker Support
```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build manually
docker build -t courtlens .
docker run -p 5000:5000 courtlens
```

## Environment Variables
Create a `.env` file:
```
SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO
```

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer
This application is for educational and research purposes only. Please respect the website's terms of service and use responsibly.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer
This tool is for educational and research purposes only. Users are responsible for complying with the Delhi High Court's terms of service and applicable laws.
