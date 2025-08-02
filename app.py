import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from scraper import DelhiHighCourtScraper
import io

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///courtlens.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database Models
class CaseRecord(db.Model):
    """Case information storage"""
    __tablename__ = 'cases'
    
    id = db.Column(db.Integer, primary_key=True)
    case_type = db.Column(db.String(100), nullable=False)
    case_number = db.Column(db.String(100), nullable=False)
    case_year = db.Column(db.Integer, nullable=False)
    diary_number = db.Column(db.String(100))
    parties = db.Column(db.Text)
    filing_date = db.Column(db.Date)
    next_hearing_date = db.Column(db.Date)
    listing_date = db.Column(db.String(100))
    court_number = db.Column(db.String(50))
    status = db.Column(db.String(100))
    pdf_links = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    raw_response = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'case_type': self.case_type,
            'case_number': self.case_number,
            'case_year': self.case_year,
            'diary_number': self.diary_number,
            'parties': self.parties,
            'filing_date': self.filing_date.isoformat() if self.filing_date else None,
            'next_hearing_date': self.next_hearing_date.isoformat() if self.next_hearing_date else None,
            'listing_date': self.listing_date,
            'court_number': self.court_number,
            'status': self.status,
            'pdf_links': json.loads(self.pdf_links) if self.pdf_links else [],
            'created_at': self.created_at.isoformat()
        }

class SearchLog(db.Model):
    """Search query logging"""
    __tablename__ = 'search_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    search_params = db.Column(db.Text, nullable=False)  # JSON string
    success = db.Column(db.Boolean, nullable=False)
    error_message = db.Column(db.Text)
    results_count = db.Column(db.Integer, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)

# Initialize scraper
scraper_config = {
    'tesseract_path': os.getenv('TESSERACT_PATH', 'tesseract'),
    'save_raw': os.getenv('DEBUG', 'False').lower() == 'true'
}
scraper = DelhiHighCourtScraper(scraper_config)

# Routes
@app.route('/')
def index():
    """Main dashboard page"""
    recent_searches = SearchLog.query.order_by(SearchLog.timestamp.desc()).limit(10).all()
    total_searches = SearchLog.query.count()
    successful_searches = SearchLog.query.filter_by(success=True).count()
    
    stats = {
        'total_searches': total_searches,
        'successful_searches': successful_searches,
        'success_rate': round((successful_searches / total_searches * 100) if total_searches > 0 else 0, 1)
    }
    
    return render_template('index.html', recent_searches=recent_searches, stats=stats)

@app.route('/search', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def search_case():
    """Search for case information"""
    if request.method == 'GET':
        case_types = scraper.get_case_types()
        years = scraper.get_years()
        return render_template('search.html', case_types=case_types, years=years)
    
    try:
        # Get form data
        case_type = request.form.get('case_type', '').strip()
        case_number = request.form.get('case_number', '').strip()
        case_year = request.form.get('case_year', '').strip()
        captcha_code = request.form.get('captcha_code', '').strip()
        
        # Validate input
        if not all([case_type, case_number, case_year]):
            flash('All fields are required', 'error')
            return redirect(url_for('search_case'))
        
        # Log search attempt
        search_params = {
            'case_type': case_type,
            'case_number': case_number,
            'case_year': case_year,
            'has_captcha': bool(captcha_code)
        }
        
        # Perform search
        logger.info(f"Searching case: {case_type} {case_number}/{case_year}")
        result = scraper.search_case(case_type, case_number, case_year, captcha_code)
        
        if result.get('error'):
            # Log failed search
            log_entry = SearchLog(
                search_params=json.dumps(search_params),
                success=False,
                error_message=result['error'],
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent', '')
            )
            db.session.add(log_entry)
            db.session.commit()
            
            flash(f"Search failed: {result['error']}", 'error')
            return redirect(url_for('search_case'))
        
        # Process successful results
        cases = result.get('cases', [])
        saved_cases = []
        
        for case_data in cases:
            # Save to database
            case_record = CaseRecord(
                case_type=case_type,
                case_number=case_number,
                case_year=int(case_year),
                diary_number=case_data.get('diary_number'),
                parties=case_data.get('parties'),
                listing_date=case_data.get('listing_date'),
                court_number=case_data.get('court_number'),
                pdf_links=json.dumps(case_data.get('pdf_links', [])),
                raw_response=json.dumps(result) if scraper_config.get('save_raw') else None
            )
            
            db.session.add(case_record)
            saved_cases.append(case_record)
        
        # Log successful search
        log_entry = SearchLog(
            search_params=json.dumps(search_params),
            success=True,
            results_count=len(cases),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        db.session.add(log_entry)
        db.session.commit()
        
        flash(f"Found {len(cases)} case(s)", 'success')
        return render_template('results.html', cases=saved_cases, search_params=search_params)
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        flash(f"An error occurred: {str(e)}", 'error')
        return redirect(url_for('search_case'))

@app.route('/api/case-types')
def api_case_types():
    """API endpoint for case types"""
    try:
        case_types = scraper.get_case_types()
        return jsonify({'success': True, 'case_types': case_types})
    except Exception as e:
        logger.error(f"API case types error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/years')
def api_years():
    """API endpoint for available years"""
    try:
        years = scraper.get_years()
        return jsonify({'success': True, 'years': years})
    except Exception as e:
        logger.error(f"API years error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/captcha')
def api_captcha():
    """API endpoint to get new CAPTCHA"""
    try:
        captcha_info = scraper._get_captcha_info()
        if captcha_info:
            return jsonify({'success': True, 'captcha': captcha_info})
        else:
            return jsonify({'success': False, 'error': 'Failed to get CAPTCHA'}), 500
    except Exception as e:
        logger.error(f"API CAPTCHA error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download/<int:case_id>/<int:link_index>')
@limiter.limit("5 per minute")
def download_pdf(case_id, link_index):
    """Download PDF file"""
    try:
        case = CaseRecord.query.get_or_404(case_id)
        pdf_links = json.loads(case.pdf_links) if case.pdf_links else []
        
        if link_index >= len(pdf_links):
            flash('PDF link not found', 'error')
            return redirect(url_for('index'))
        
        pdf_url = pdf_links[link_index]['url']
        
        # Download PDF
        result = scraper.download_pdf(pdf_url)
        
        if result.get('error'):
            flash(f"Download failed: {result['error']}", 'error')
            return redirect(url_for('index'))
        
        # Return PDF file
        return send_file(
            io.BytesIO(result['content']),
            as_attachment=True,
            download_name=result['filename'],
            mimetype='application/pdf'
        )
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        flash(f"Download failed: {str(e)}", 'error')
        return redirect(url_for('index'))

@app.route('/history')
def search_history():
    """View search history"""
    page = request.args.get('page', 1, type=int)
    searches = SearchLog.query.order_by(SearchLog.timestamp.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('history.html', searches=searches)

@app.route('/case/<int:case_id>')
def view_case(case_id):
    """View detailed case information"""
    case = CaseRecord.query.get_or_404(case_id)
    return render_template('case_detail.html', case=case)

# CLI Commands
@app.cli.command()
def init_db():
    """Initialize database"""
    db.create_all()
    logger.info("Database initialized successfully")

@app.cli.command()
def test_scraper():
    """Test scraper functionality"""
    logger.info("Testing scraper...")
    
    # Test getting case types
    case_types = scraper.get_case_types()
    logger.info(f"Case types: {case_types}")
    
    # Test getting years
    years = scraper.get_years()
    logger.info(f"Years: {years}")
    
    # Test CAPTCHA
    captcha_info = scraper._get_captcha_info()
    logger.info(f"CAPTCHA info: {captcha_info}")
    
    logger.info("Scraper test completed")

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

@app.errorhandler(429)
def ratelimit_handler(error):
    return render_template('error.html', error="Rate limit exceeded. Please try again later."), 429

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=5000)
