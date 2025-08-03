import os
import json
import sqlite3
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
import io

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

@app.template_filter('fromjson')
def fromjson_filter(value):
    try:
        return json.loads(value) if value else {}
    except (ValueError, TypeError):
        return {}

@app.template_filter('formatdate')
def formatdate_filter(value, format='%Y-%m-%d %H:%M'):
    if not value:
        return 'N/A'
    try:
        if hasattr(value, 'strftime'):
            return value.strftime(format)
        if isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                return dt.strftime(format)
            except:
                dt = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                return dt.strftime(format)
        return str(value)
    except Exception:
        return str(value) if value else 'N/A'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('court_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATABASE_PATH = 'courtlens.db'

def init_database():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_type TEXT NOT NULL,
                case_number TEXT NOT NULL,
                case_year INTEGER NOT NULL,
                diary_number TEXT,
                parties TEXT,
                filing_date TEXT,
                next_hearing_date TEXT,
                listing_date TEXT,
                court_number TEXT,
                status TEXT,
                pdf_links TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                raw_response TEXT
            )''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_params TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                results_count INTEGER DEFAULT 0,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT
            )''')
        
        cursor.execute("PRAGMA table_info(search_logs)")
        columns = [column[1] for column in cursor.fetchall()]
            
        if 'error_message' not in columns:
            cursor.execute('ALTER TABLE search_logs ADD COLUMN error_message TEXT')
            
        if 'results_count' not in columns:
            cursor.execute('ALTER TABLE search_logs ADD COLUMN results_count INTEGER DEFAULT 0')
            
        if 'ip_address' not in columns:
            cursor.execute('ALTER TABLE search_logs ADD COLUMN ip_address TEXT')
            
        if 'user_agent' not in columns:
            cursor.execute('ALTER TABLE search_logs ADD COLUMN user_agent TEXT')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

scraper_config = {
    'tesseract_path': os.getenv('TESSERACT_PATH', 'tesseract'),
    'save_raw': False
}

try:
    from scraper import DelhiHighCourtScraper
    scraper = DelhiHighCourtScraper(scraper_config)
    logger.info("Scraper initialized successfully")
except ImportError:
    logger.error("Could not import scraper module")
    scraper = None

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def insert_case(case_data):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO cases (
                case_number, case_type, status, petitioner, respondent,
                petitioner_advocate, respondent_advocate, next_hearing_date,
                last_hearing_date, court_number, diary_number, order_details,
                order_link, raw_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            case_data.get('case_number'),
            case_data.get('case_type'),
            case_data.get('status'),
            case_data.get('petitioner'),
            case_data.get('respondent'),
            case_data.get('petitioner_advocate'),
            case_data.get('respondent_advocate'),
            case_data.get('next_hearing_date'),
            case_data.get('last_hearing_date'),
            case_data.get('court_number'),
            case_data.get('diary_number'),
            case_data.get('order_details'),
            case_data.get('order_link'),
            json.dumps(case_data)))
        
        case_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Case inserted with ID: {case_id}")
        return case_id
        
    except Exception as e:
        logger.error(f"Error inserting case: {e}")
        return None

def insert_search_log(log_data):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO search_logs (
                search_params, success, error_message, results_count,
                ip_address, user_agent
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            json.dumps(log_data.get('search_params')),
            log_data.get('success'),
            log_data.get('error_message'),
            log_data.get('results_count', 0),
            log_data.get('ip_address'),
            log_data.get('user_agent')
        ))
        
        conn.commit()
        conn.close()
        logger.info("Search log inserted successfully")
        
    except Exception as e:
        logger.error(f"Error inserting search log: {e}")

def get_recent_searches(limit=10):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT search_params, success, results_count, error_message, 
                ip_address, user_agent, timestamp 
            FROM search_logs 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        searches = cursor.fetchall()
        conn.close()
        
        search_list = []
        for search in searches:
            search_list.append({
                'search_params': search[0],
                'success': search[1], 
                'results_count': search[2],
                'error_message': search[3],
                'ip_address': search[4],
                'user_agent': search[5],
                'timestamp': search[6]
})
        
        return search_list
    except Exception as e:
        logger.error(f"Error getting recent searches: {e}")
        return []

def get_search_stats():
    """Get search statistics with error handling"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM search_logs')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) as successful FROM search_logs WHERE success = 1')
        successful = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT ip_address) as unique_users FROM search_logs')
        unique_users = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_searches': total,
            'successful_searches': successful,
            'unique_users': unique_users,
            'success_rate': round((successful / total * 100), 2) if total > 0 else 0
        }
    except Exception as e:
        logger.error(f"Error getting search stats: {e}")
        return {
            'total_searches': 0,
            'successful_searches': 0,
            'unique_users': 0,
            'success_rate': 0
        }

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"]
)
limiter.init_app(app)

@app.route('/')
def index():
    try:
        stats = get_search_stats()
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        stats = {
            'total_searches': 0,
            'successful_searches': 0,
            'unique_users': 0,
            'success_rate': 0
        }
    return render_template('index.html', stats=stats)

@app.route('/search', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def search_case():
    if request.method == 'GET':
        try:
            temp_scraper = DelhiHighCourtScraper(scraper_config)
            case_types = temp_scraper.get_case_types()
            years = temp_scraper.get_years()
            return render_template('search.html', case_types=case_types, years=years)
        except Exception as e:
            logger.error(f"Error loading search form: {e}")
            flash('Error loading search form. Please try again.', 'error')
            return render_template('search.html', case_types=[], years=[])
    
    try:
        logger.info("Creating fresh scraper instance for new search...")
        fresh_scraper = DelhiHighCourtScraper(scraper_config)
        
        case_type = request.form.get('case_type', '').strip()
        case_number = request.form.get('case_number', '').strip()
        case_year = request.form.get('case_year', '').strip()
        captcha_code = request.form.get('captcha_code', '').strip()
        
        case_type_mapping = {
            'writ': 'W.P.(C)',
            'criminal': 'CRL.A.',
            'civil': 'CA',
            'arbitration': 'ARB.P.',
            'company': 'CO.PET.',
            'appeal': 'CA',
            'bail': 'BAIL APPLN.',
            'contempt': 'CONT.CAS(C)',
            'misc': 'CRL.M.C.',
            'review': 'CRL.REV.P.',
            'W.P.(C)': 'W.P.(C)',
            'W.P.(CRL)': 'W.P.(CRL)',
            'CRL.A.': 'CRL.A.',
            'CA': 'CA',
            'Writ Petition (Civil)': 'W.P.(C)',
            'Writ Petition (Criminal)': 'W.P.(CRL)',
            'Civil Appeal': 'CA',
            'Criminal Appeal': 'CRL.A.'
        }
        
        mapped_case_type = case_type_mapping.get(case_type, case_type)
        
        if not all([case_type, case_number, case_year]):
            flash('All fields are required', 'error')
            return redirect(url_for('search_case'))
        
        search_params = {
            'case_type': mapped_case_type,
            'case_number': case_number,
            'case_year': case_year,
            'has_captcha': bool(captcha_code)
        }
        
        logger.info(f"Starting search with fresh scraper: {search_params}")
        
        result = fresh_scraper.search_case(mapped_case_type, case_number, case_year)
        
        logger.info(f"Search result: {result}")
        
        if not result.get('success'):
            error_msg = result.get('error', 'Unknown error occurred')
            is_network_issue = result.get('network_issue', False)
            
            insert_search_log({
                'search_params': search_params,
                'success': False,
                'error_message': error_msg,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            })
            
            if is_network_issue:
                flash(f"Network Connection Issue: {error_msg}", 'error')
                flash("Troubleshooting Tips:", 'info')
                flash("• Check your internet connection", 'info')
                flash("• The Delhi High Court website may be temporarily down", 'info')
                flash("• Try again in a few minutes", 'info')
                flash("• If the problem persists, contact your network administrator", 'info')
            else:
                flash(f"Search failed: {error_msg}", 'error')
            
            return redirect(url_for('search_case'))
        
        cases = result.get('cases', [])
        
        if not cases:
            insert_search_log({
                'search_params': search_params,
                'success': False,
                'error_message': 'No cases found - Invalid case number or not in system',
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            })
            
            flash(f"No case found for {mapped_case_type} {case_number}/{case_year}. Please verify the case details.", 'warning')
            return redirect(url_for('search_case'))
        
        saved_cases = []
        
        for case_data in cases:
            case_id = insert_case(case_data)
            if case_id:
                case_data['id'] = case_id
                saved_cases.append(case_data)
        
        insert_search_log({
            'search_params': search_params,
            'success': True,
            'results_count': len(saved_cases),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        })
        
        flash(f"Found {len(saved_cases)} case(s)", 'success')
        return render_template('results.html', 
                            cases=saved_cases, 
                            search_params=search_params,
                            current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        
        try:
            insert_search_log({
                'search_params': {
                    'case_type': request.form.get('case_type', ''),
                    'case_number': request.form.get('case_number', ''),
                    'case_year': request.form.get('case_year', '')
                },
                'success': False,
                'error_message': f"System error: {str(e)}",
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            })
        except:
            pass
        
        flash(f"An unexpected error occurred: {str(e)}", 'error')
        return redirect(url_for('search_case'))

@app.route('/api/case-types')
def api_case_types():
    try:
        if not scraper:
            return jsonify({'success': False, 'error': 'Scraper not available'}), 500
        
        case_types = scraper.get_case_types()
        return jsonify({'success': True, 'case_types': case_types})
    except Exception as e:
        logger.error(f"API case types error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/years')
def api_years():
    try:
        if not scraper:
            return jsonify({'success': False, 'error': 'Scraper not available'}), 500
        
        years = scraper.get_years()
        return jsonify({'success': True, 'years': years})
    except Exception as e:
        logger.error(f"API years error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/captcha')
def api_captcha():
    try:
        from scraper import DelhiHighCourtScraper
        temp_scraper = DelhiHighCourtScraper()
        
        captcha_info = temp_scraper.get_captcha_info()
        if captcha_info and captcha_info.get('has_captcha'):
            return jsonify({'success': True, 'captcha_info': captcha_info})
        else:
            return jsonify({'success': False, 'error': 'No CAPTCHA available'}), 500
    except Exception as e:
        logger.error(f"API CAPTCHA error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/history')
def search_history():
    try:
        searches_list = get_recent_searches(50)
        if searches_list is None:
            searches_list = []
        
        class SearchesData:
            def __init__(self, items, total):
                self.items = items
                self.total = total
                self.pages = 1
                self.has_prev = False
                self.has_next = False
        
        searches = SearchesData(searches_list, len(searches_list))
        return render_template('history.html', searches=searches)
    except Exception as e:
        logger.error(f"Search history error: {e}")
        searches = SearchesData([], 0)
        return render_template('history.html', searches=searches)

@app.route('/debug')
def debug_info():
    """Debug endpoint to check scraper status"""
    if not scraper:
        return jsonify({
            'scraper_available': False,
            'error': 'Scraper not initialized'
        })
    
    try:
        randomid, csrf_token = scraper.get_session_data(force_refresh=True)
        
        debug_info = {
            'scraper_available': True,
            'session_data': {
                'randomid': randomid[:10] + '...' if randomid else None,
                'csrf_token': csrf_token[:10] + '...' if csrf_token else None,
                'session_valid': bool(randomid and csrf_token)
            },
            'case_types_count': len(scraper.get_case_types()),
            'years_count': len(scraper.get_years()),
            'base_url': scraper.base_url,
            'request_count': scraper.request_count
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({
            'scraper_available': True,
            'error': str(e),
            'session_data': {'session_valid': False}
        })

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return render_template('error.html', error="Internal server error"), 500

@app.errorhandler(429)
def ratelimit_handler(error):
    return render_template('error.html', error="Rate limit exceeded. Please try again later."), 429

if __name__ == '__main__':
    try:
        init_database()
        logger.info("Starting CourtLens application...")
        app.run(debug=False, host='0.0.0.0', port=5000)
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        print(f"Error: {e}")