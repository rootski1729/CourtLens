# CourtLens - Delhi High Court Case Search System

## Overview
CourtLens is a comprehensive web application that fetches case information from the **Delhi High Court** (https://delhihighcourt.nic.in/). It provides a clean, user-friendly interface for searching cases and viewing detailed results with proper session management and security handling.

## Court Chosen: Delhi High Court
- **Target**: Delhi High Court (https://delhihighcourt.nic.in/)
- **Reason**: Reliable API endpoint with consistent data structure
- **CAPTCHA Strategy**: Automatic CSRF token extraction from JavaScript, session management with fresh tokens per request

## Features
- **Simple UI**: Clean HTML form with dropdowns for Case Type, Case Number, Filing Year
- **Backend Scraping**: Programmatic requests to Delhi High Court with CAPTCHA bypass
- **Data Parsing**: Extracts parties' names, filing dates, next hearing dates, order/judgment links
- **Database Storage**: SQLite logging of every query and raw response  
- **PDF Downloads**: Links to order/judgment PDFs when available
- **Error Handling**: User-friendly messages for invalid cases or site downtime
- **Session Management**: Fresh scraper instances per search for reliability
- **Rate Limiting**: API protection against excessive requests

## Tech Stack
- **Backend**: Python Flask 3.0
- **Database**: SQLite with proper schema
- **Web Scraping**: Requests + BeautifulSoup with CSRF handling
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **Security**: Flask-Limiter, CSRF token management

## CAPTCHA Strategy
1. **Session Initialization**: Fresh session with proper headers for each search
2. **Token Extraction**: Automatic CSRF token extraction from JavaScript on main page
3. **Dynamic Headers**: Proper User-Agent, Referer, and X-Requested-With headers
4. **Cookie Management**: Automatic session cookie handling
5. **Fresh Sessions**: New scraper instance per search to avoid stale sessions

## Quick Start

### Prerequisites
- Python 3.8+
- Virtual environment (recommended)

### Installation
```bash
# Clone the repository
git clone https://github.com/rootski1729/CourtLens.git
cd CourtLens

# Create virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python setup_db.py

# Run the application
python app_simple.py
```

### Environment Variables (Optional)
Create a `.env` file:
```env
SECRET_KEY=your-secret-key-here
TESSERACT_PATH=tesseract  # For future OCR features
DATABASE_PATH=courtlens.db
```

## Usage

1. **Access**: Open http://localhost:5000 in your browser
2. **Search**: Select Case Type, enter Case Number and Year
3. **Results**: View parsed case details including:
   - Parties' names (Petitioner/Respondent)
   - Advocate details
   - Filing and next hearing dates
   - Order/judgment PDF links (when available)
   - Case status and court number
4. **Download**: Click PDF links to download orders/judgments
5. **History**: View search history with timestamps

## Sample Cases for Testing
- **W.P.(C) 7608/2019**: GREAT LEGALISATION MOVEMENT INDIA TRUST vs UNION OF INDIA AND ORS.
- **W.P.(C) 1234/2020**: Test various case numbers
- **CRL.A. 100/2021**: Criminal appeals

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
