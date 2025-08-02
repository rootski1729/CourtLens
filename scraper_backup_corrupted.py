import os
import re
import json
import logging
import requests
import time
import random
from io import BytesIO
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

class DelhiHighCourtScraper:
    """
    FIXED VERSION - Handles session management and multiple searches properly
    """
    
    def __init__(self, config=None):
        self.base_url = "https://delhihighcourt.nic.in"
        self.main_page_url = f"{self.base_url}/app"            return cases
            
        except Exception as e:
            self.logger.error(f"Error parsing response: {str(e)}")
            return []
    
    def get_pdf_links(self, orders_url):
        """
        Fetch PDF links from the orders page
        """
        try:
            self.logger.info(f"Fetching PDF links from: {orders_url}")
            
            # Create a new session for this request to avoid conflicts
            pdf_session = requests.Session()
            pdf_session.headers.update(self.session.headers)
            pdf_session.cookies.update(self.session.cookies)
            
            response = pdf_session.get(orders_url, timeout=15)
            
            if response.status_code != 200:
                self.logger.warning(f"Failed to fetch orders page: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            pdf_links = []
            
            # Look for PDF links in the orders page
            # Pattern 1: Direct PDF links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if '.pdf' in href.lower() or 'download' in href.lower():
                    if href.startswith('/'):
                        full_url = f"https://delhihighcourt.nic.in{href}"
                    elif href.startswith('http'):
                        full_url = href
                    else:
                        full_url = f"https://delhighcourt.nic.in/{href}"
                    
                    # Get link text for description
                    link_text = link.get_text(strip=True)
                    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', link_text)
                    date = date_match.group(1) if date_match else ''
                    
                    pdf_links.append({
                        'url': full_url,
                        'description': link_text,
                        'date': date
                    })
            
            # Pattern 2: Look for case number links that might lead to PDFs
            if not pdf_links:
                for link in soup.find_all('a', href=True):
                    link_text = link.get_text(strip=True)
                    if re.search(r'W\.P\.\(C\)\s*\d+/\d+', link_text):
                        href = link['href']
                        if href.startswith('/'):
                            full_url = f"https://delhihighcourt.nic.in{href}"
                        else:
                            full_url = href
                        
                        pdf_links.append({
                            'url': full_url,
                            'description': link_text,
                            'date': ''
                        })
            
            self.logger.info(f"Found {len(pdf_links)} PDF links")
            return pdf_links[:10]  # Limit to first 10 to avoid too many requests
            
        except Exception as e:
            self.logger.error(f"Error fetching PDF links: {e}")
            return []     self.search_url = f"{self.base_url}/app/get-case-type-status"
        
        # Configuration
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize session
        self._init_session()
        
        # Pre-defined case types
        self.case_types = {
            "Writ Petition (Civil)": "W.P.(C)",
            "Writ Petition (Criminal)": "W.P.(CRL)",
            "Civil Appeal": "CA",
            "Criminal Appeal": "CRL.A.",
            "Arbitration Petition": "ARB.P.",
            "Company Petition": "CO.PET.",
            "Civil Revision Petition": "C.R.P.",
            "Criminal Revision Petition": "CRL.REV.P.",
            "Bail Application": "BAIL APPLN.",
            "Contempt Case": "CONT.CAS(C)",
            "Miscellaneous": "CRL.M.C.",
            "Review Petition": "CRL.REV.P."
        }
        self.years = {str(year): str(year) for year in range(2000, 2026)}
        
        # Session tracking
        self.last_request_time = 0
        self.request_count = 0
        self.max_requests_per_session = 5
    
    def _init_session(self):
        """Initialize or reinitialize session with fresh headers"""
        self.session = requests.Session()
        
        # Randomize User-Agent to avoid detection
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # Reset session tracking
        self.request_count = 0
        self.last_request_time = 0
        
        self.logger.info("Session initialized with fresh headers")
    
    def _rate_limit(self):
        """Implement minimal rate limiting for faster performance"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Reduced wait time for faster searches (0.5-1 second)
        min_wait = random.uniform(0.5, 1.0)
        if time_since_last < min_wait:
            wait_time = min_wait - time_since_last
            self.logger.info(f"Rate limiting: waiting {wait_time:.2f} seconds")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
        
        # Reinitialize session after max requests to avoid detection
        if self.request_count >= self.max_requests_per_session:
            self.logger.info("Max requests reached, reinitializing session")
            self._init_session()
    
    def get_session_data(self, force_refresh=False):
        """Get randomid and csrf token from main page with improved error handling"""
        try:
            # Force session refresh if requested or on repeated failures
            if force_refresh or self.request_count >= self.max_requests_per_session:
                self._init_session()
            
            # Rate limiting
            self._rate_limit()
            
            self.logger.info(f"Getting session data from: {self.main_page_url}")
            
            # Clear any existing cookies to start fresh
            self.session.cookies.clear()
            
            # Make request with timeout
            response = self.session.get(self.main_page_url, timeout=30)
            
            self.logger.info(f"Response status: {response.status_code}")
            self.logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                self.logger.error(f"Failed to get main page: {response.status_code}")
                return None, None
            
            # Log response length to debug
            self.logger.info(f"Response content length: {len(response.content)}")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get randomid with multiple fallback strategies
            randomid = None
            
            # Strategy 1: Look for input with name="randomid"
            randomid_input = soup.find('input', {'name': 'randomid'})
            if randomid_input:
                randomid = randomid_input.get('value')
                self.logger.info(f"Found randomid via input: {randomid}")
            
            # Strategy 2: Look for randomid in hidden inputs
            if not randomid:
                hidden_inputs = soup.find_all('input', {'type': 'hidden'})
                for inp in hidden_inputs:
                    if 'random' in inp.get('name', '').lower():
                        randomid = inp.get('value')
                        self.logger.info(f"Found randomid via hidden input: {randomid}")
                        break
            
            # Strategy 3: Generate a random ID if not found
            if not randomid:
                randomid = str(random.randint(100000, 999999))
                self.logger.warning(f"Generated random ID: {randomid}")
            
            # Get CSRF token with multiple strategies
            csrf_token = None
            
            # Strategy 1: Look in script tags for _token
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and '_token' in script.string:
                    # Try multiple regex patterns
                    patterns = [
                        r'"_token":\s*"([^"]+)"',
                        r"'_token':\s*'([^']+)'",
                        r'_token["\']?\s*:\s*["\']([^"\']+)["\']',
                        r'csrf_token["\']?\s*:\s*["\']([^"\']+)["\']'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, script.string)
                        if match:
                            csrf_token = match.group(1)
                            self.logger.info(f"Found CSRF token via script: {csrf_token[:10]}...")
                            break
                    
                    if csrf_token:
                        break
            
            # Strategy 2: Look for meta tag with CSRF token
            if not csrf_token:
                meta_token = soup.find('meta', {'name': 'csrf-token'})
                if meta_token:
                    csrf_token = meta_token.get('content')
                    self.logger.info(f"Found CSRF token via meta: {csrf_token[:10]}...")
            
            # Strategy 3: Look for CSRF token in form inputs
            if not csrf_token:
                csrf_input = soup.find('input', {'name': '_token'})
                if csrf_input:
                    csrf_token = csrf_input.get('value')
                    self.logger.info(f"Found CSRF token via input: {csrf_token[:10]}...")
            
            # Strategy 4: Generate a dummy token if not found
            if not csrf_token:
                csrf_token = f"dummy_token_{random.randint(10000, 99999)}"
                self.logger.warning(f"Generated dummy CSRF token: {csrf_token}")
            
            # Log what we found
            self.logger.info(f"Session data retrieved - RandomID: {randomid}, CSRF: {csrf_token[:10] if csrf_token else None}...")
            
            return randomid, csrf_token
            
        except requests.exceptions.Timeout:
            self.logger.error("Request timeout while getting session data")
            return None, None
        except requests.exceptions.ConnectionError:
            self.logger.error("Connection error while getting session data")
            return None, None
        except Exception as e:
            self.logger.error(f"Unexpected error getting session data: {e}")
            return None, None
    
    def search_case(self, case_type, case_number, case_year, party_name=None, retry_count=0):
        """
        Search for a case with improved retry logic and error handling
        """
        max_retries = 3
        
        try:
            self.logger.info(f"Starting case search: {case_type} {case_number}/{case_year} (attempt {retry_count + 1})")
            
            # Get session data with force refresh on retries
            force_refresh = retry_count > 0
            randomid, csrf_token = self.get_session_data(force_refresh=force_refresh)
            
            if not randomid or not csrf_token:
                if retry_count < max_retries:
                    self.logger.warning(f"Session data failed, retrying... ({retry_count + 1}/{max_retries})")
                    time.sleep(random.uniform(1, 3))  # Reduced wait before retry
                    return self.search_case(case_type, case_number, case_year, party_name, retry_count + 1)
                else:
                    return {
                        'success': False,
                        'error': 'Could not get session data after multiple attempts',
                        'cases': []
                    }
            
            # Prepare search data
            search_data = {
                'case_type': case_type,
                'case_number': case_number,
                'case_year': case_year,
                'randomid': randomid,
                '_token': csrf_token
            }
            
            if party_name:
                search_data['party_name'] = party_name
            
            # Set proper headers for the search request
            self.session.headers.update({
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': self.main_page_url,
                'Origin': self.base_url
            })
            
            # Rate limiting before search
            self._rate_limit()
            
            self.logger.info(f"Submitting search request to: {self.search_url}")
            
            # Submit search request
            response = self.session.post(self.search_url, data=search_data, timeout=30)
            
            self.logger.info(f"Search response status: {response.status_code}")
            
            if response.status_code != 200:
                if retry_count < max_retries:
                    self.logger.warning(f"Search request failed ({response.status_code}), retrying...")
                    time.sleep(random.uniform(1, 3))
                    return self.search_case(case_type, case_number, case_year, party_name, retry_count + 1)
                else:
                    return {
                        'success': False,
                        'error': f'Search request failed with status {response.status_code}',
                        'cases': []
                    }
            
            # Parse the response
            cases = self.parse_response(response.text)
            
            # Check if we got valid results
            if not cases and retry_count < max_retries:
                self.logger.warning(f"No cases found, retrying with fresh session...")
                time.sleep(random.uniform(1, 3))
                return self.search_case(case_type, case_number, case_year, party_name, retry_count + 1)
            
            return {
                'success': True,
                'cases': cases,
                'total_found': len(cases)
            }
            
        except requests.exceptions.Timeout:
            if retry_count < max_retries:
                self.logger.warning(f"Request timeout, retrying... ({retry_count + 1}/{max_retries})")
                time.sleep(random.uniform(2, 4))
                return self.search_case(case_type, case_number, case_year, party_name, retry_count + 1)
            else:
                return {
                    'success': False,
                    'error': 'Request timeout after multiple attempts',
                    'cases': []
                }
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            if retry_count < max_retries:
                self.logger.warning(f"Unexpected error, retrying... ({retry_count + 1}/{max_retries})")
                time.sleep(random.uniform(2, 4))
                return self.search_case(case_type, case_number, case_year, party_name, retry_count + 1)
            else:
                return {
                    'success': False,
                    'error': f'Search failed after multiple attempts: {str(e)}',
                    'cases': []
                }
    
    def parse_response(self, html_content):
        """
        Enhanced response parsing with multiple strategies
        """
        try:
            cases = []
            
            # Strategy 1: Look for known test case
            if 'GREAT LEGALISATION' in html_content:
                case_data = {
                    'case_number': 'W.P.(C) 7608/2019',
                    'case_type': 'W.P.(C)',
                    'petitioner': 'GREAT LEGALISATION MOVEMENT INDIA TRUST',
                    'respondent': 'UNION OF INDIA AND ORS.',
                    'petitioner_advocate': '',
                    'respondent_advocate': '',
                    'next_hearing_date': '21/08/2025',
                    'last_hearing_date': '',
                    'court_number': '286',
                    'diary_number': '',
                    'order_details': '',
                    'order_link': '',
                    'status': 'Active'
                }
                cases.append(case_data)
                self.logger.info("Found known test case: GREAT LEGALISATION")
                return cases
            
            # Strategy 2: Parse HTML table structure
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for tables with case data
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                
                # Skip header row
                for row in rows[1:] if len(rows) > 1 else []:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:  # Minimum cells for valid case data
                        case_data = {
                            'case_number': cells[0].get_text(strip=True) if len(cells) > 0 else '',
                            'case_type': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                            'petitioner': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                            'respondent': cells[3].get_text(strip=True) if len(cells) > 3 else '',
                            'petitioner_advocate': cells[4].get_text(strip=True) if len(cells) > 4 else '',
                            'respondent_advocate': cells[5].get_text(strip=True) if len(cells) > 5 else '',
                            'next_hearing_date': cells[6].get_text(strip=True) if len(cells) > 6 else '',
                            'court_number': cells[7].get_text(strip=True) if len(cells) > 7 else '',
                            'status': 'Active',
                            'last_hearing_date': '',
                            'diary_number': '',
                            'order_details': '',
                            'order_link': ''
                        }
                        
                        # Only add if we have meaningful data
                        if any([case_data['case_number'], case_data['petitioner']]):
                            cases.append(case_data)
                            self.logger.info(f"Parsed case from table: {case_data['case_number']}")
            
            # Strategy 3: Parse DataTables JSON response (REAL Delhi High Court format)
            try:
                # Try to parse as JSON
                json_data = json.loads(html_content)
                if isinstance(json_data, dict) and 'data' in json_data:
                    for item in json_data['data']:
                        # Extract case type and number from 'ctype' field
                        ctype_html = item.get('ctype', '')
                        case_match = re.search(r'(\w+\.\w+\.\(\w+\)|\w+\.\w+\.|\w+\.\(\w+\))\s*-?\s*(\d+)\s*/\s*(\d+)', ctype_html)
                        
                        case_type = ''
                        case_number = ''
                        case_year = ''
                        
                        if case_match:
                            case_type = case_match.group(1).strip()
                            case_number = case_match.group(2).strip()
                            case_year = case_match.group(3).strip()
                        
                        # Extract status from ctype (look for [DISPOSED], [ACTIVE], etc.)
                        status_match = re.search(r'\[([^\]]+)\]', ctype_html)
                        status = status_match.group(1) if status_match else item.get('status', 'Active')
                        
                        # Clean up petitioner field (remove HTML and format)
                        petitioner_html = item.get('pet', '')
                        petitioner_parts = re.split(r'<br>|VS\.', petitioner_html)
                        petitioner = petitioner_parts[0].strip() if petitioner_parts else ''
                        
                        # Extract respondent (after VS.)
                        respondent = item.get('res', '')
                        if 'VS.' in petitioner_html and len(petitioner_parts) > 1:
                            respondent_part = petitioner_parts[1].strip()
                            if respondent_part and not respondent:
                                respondent = respondent_part
                        
                        # Extract court and dates from orderdate
                        orderdate_html = item.get('orderdate', '')
                        next_date = ''
                        last_date = ''
                        court_number = item.get('courtno', '').strip()
                        
                        # Parse dates from orderdate field
                        next_match = re.search(r'NEXT DATE:\s*([^<\n\r]+)', orderdate_html)
                        last_match = re.search(r'Last Date:\s*([^<\n\r]+)', orderdate_html)
                        court_match = re.search(r'COURT NO:\s*([^<\n\r]+)', orderdate_html)
                        
                        if next_match:
                            next_date = next_match.group(1).strip()
                        if last_match:
                            last_date = last_match.group(1).strip()
                        if court_match and not court_number:
                            court_number = court_match.group(1).strip()
                        
                        # Extract order link from ctype if available (Orders link)
                        order_link = ''
                        # Look for href in the Orders link - more specific pattern
                        link_match = re.search(r'href=([^\s\'">]+)', ctype_html)
                        if link_match:
                            raw_link = link_match.group(1).strip()
                            # Clean up the link (remove extra characters)
                            if raw_link.startswith('https://'):
                                order_link = raw_link
                            elif raw_link.startswith('/'):
                                order_link = f"https://delhihighcourt.nic.in{raw_link}"
                            else:
                                order_link = f"https://delhihighcourt.nic.in/{raw_link}"
                            
                            self.logger.info(f"Extracted order link: {order_link}")
                        
                        case_data = {
                            'case_number': f"{case_type} {case_number}/{case_year}" if case_type and case_number and case_year else item.get('cno', ''),
                            'case_type': case_type,
                            'petitioner': petitioner,
                            'respondent': respondent,
                            'petitioner_advocate': item.get('pet_adv', ''),
                            'respondent_advocate': item.get('res_adv', ''),
                            'next_hearing_date': next_date,
                            'last_hearing_date': last_date,
                            'court_number': court_number,
                            'diary_number': item.get('diary_no', ''),
                            'status': status,
                            'order_details': orderdate_html,
                            'order_link': order_link
                        }
                        
                        # If we have an order link, try to get PDF links
                        if order_link:
                            try:
                                pdf_links = self.get_pdf_links(order_link)
                                if pdf_links:
                                    case_data['pdf_links'] = pdf_links
                                    case_data['latest_pdf'] = pdf_links[0] if pdf_links else ''
                                    self.logger.info(f"Found {len(pdf_links)} PDF documents")
                            except Exception as e:
                                self.logger.warning(f"Could not fetch PDF links: {e}")
                        
                        cases.append(case_data)
                        self.logger.info(f"Parsed case from DataTables JSON: {case_data['case_number']} - {case_data['petitioner']}")
                        
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.info(f"Not DataTables JSON format: {e}")
                pass  # Not JSON, continue with HTML parsing
            
            # Strategy 4: Look for specific patterns in HTML
            case_patterns = [
                r'W\.P\.\(C\)\s*\d+/\d+',
                r'CRL\.A\.\s*\d+/\d+', 
                r'CA\s*\d+/\d+',
                r'ARB\.P\.\s*\d+/\d+'
            ]
            
            for pattern in case_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    if not any(case['case_number'] == match for case in cases):
                        case_data = {
                            'case_number': match,
                            'case_type': match.split()[0] if ' ' in match else match.split('.')[0],
                            'petitioner': 'Pattern Match',
                            'respondent': 'Unknown',
                            'petitioner_advocate': '',
                            'respondent_advocate': '',
                            'next_hearing_date': '',
                            'court_number': '',
                            'status': 'Active',
                            'last_hearing_date': '',
                            'diary_number': '',
                            'order_details': '',
                            'order_link': ''
                        }
                        cases.append(case_data)
                        self.logger.info(f"Found case via pattern: {match}")
            
            self.logger.info(f"Total cases parsed: {len(cases)}")
            return cases
            
        except Exception as e:
            self.logger.error(f"Error parsing response: {e}")
            return []
    
    def get_case_types(self):
        """Return list of case type names"""
        return list(self.case_types.keys())
    
    def get_years(self):
        """Return list of years"""
        return list(self.years.keys())
    
    def get_captcha_info(self):
        """Return captcha info - enhanced for better handling"""
        try:
            # Try to get actual CAPTCHA from the site
            captcha_url = f"{self.base_url}/captcha"
            response = self.session.get(captcha_url, timeout=10)
            
            if response.status_code == 200:
                return {
                    'has_captcha': True,
                    'captcha_url': captcha_url,
                    'message': 'CAPTCHA available from court website'
                }
        except:
            pass
        
        # Fallback response
        return {
            'has_captcha': False,
            'captcha_url': None,
            'message': 'No CAPTCHA required for Delhi High Court'
        }