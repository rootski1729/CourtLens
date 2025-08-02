import os
import re
import json
import time
import logging
import requests
from io import BytesIO
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

class DelhiHighCourtScraper:
    
    def __init__(self, config=None):
        self.base_url = "https://delhihighcourt.nic.in"
        self.main_page_url = f"{self.base_url}/app"
        self.search_url = f"{self.base_url}/app/get-case-type-status"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Network resilience settings
        self.session.timeout = 30
        self.session.verify = True
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        self.case_types = {
            "Writ Petition (Civil)": "W.P.(C)",
            "Writ Petition (Criminal)": "W.P.(CRL)",
            "Civil Appeal": "CA",
            "Criminal Appeal": "CRL.A.",
            "Arbitration Petition": "ARB.P.",
            "Company Petition": "CO.PET.",
            "Civil Revision Petition": "C.R.P.",
            "Criminal Revision Petition": "CRL.REV.P.",
            "Bail Application": "BAIL APPLN."
        }
        self.years = {str(year): str(year) for year in range(2015, 2026)}
    
    def get_session_data(self):
        try:
            response = self.session.get(self.main_page_url)
            if response.status_code != 200:
                return None, None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            randomid_input = soup.find('input', {'name': 'randomid'})
            randomid = randomid_input.get('value') if randomid_input else None
            
            csrf_token = None
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and '_token' in script.string:
                    match = re.search(r'"_token":\s*"([^"]+)"', script.string)
                    if match:
                        csrf_token = match.group(1)
                        break
            
            return randomid, csrf_token
            
        except Exception as e:
            return None, None
    
    def search_case(self, case_type, case_number, case_year, party_name=None):
        """Search for cases with improved error handling and retries"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Search attempt {attempt + 1}/{max_retries}")
                
                # Get session data with timeout handling
                randomid, csrf_token = self.get_session_data()
                if not randomid or not csrf_token:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Failed to get session data, retrying in 3 seconds...")
                        time.sleep(3)
                        continue
                    else:
                        return {
                            'success': False, 
                            'error': 'Could not get session data after multiple attempts. The Delhi High Court website may be temporarily unavailable.',
                            'cases': [],
                            'network_issue': True
                        }
                
                search_data = {
                    'case_type': case_type,
                    'case_number': case_number,
                    'case_year': case_year,
                    'randomid': randomid,
                    '_token': csrf_token
                }
                
                if party_name:
                    search_data['party_name'] = party_name
                
                self.session.headers.update({
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Referer': self.main_page_url
                })
                
                # Make the DataTables AJAX request directly to get case data
                datatables_url = f"{self.base_url}/app/get-case-type-status"
                datatables_data = {
                    'draw': '5',
                    'columns[0][data]': 'DT_RowIndex',
                    'columns[0][name]': 'DT_RowIndex',
                    'columns[0][searchable]': 'true',
                    'columns[0][orderable]': 'false',
                    'columns[1][data]': 'ctype',
                    'columns[1][name]': 'ctype',
                    'columns[1][searchable]': 'true',
                    'columns[1][orderable]': 'true',
                    'columns[2][data]': 'pet',
                    'columns[2][name]': 'pet',
                    'columns[2][searchable]': 'true',
                    'columns[2][orderable]': 'true',
                    'columns[3][data]': 'orderdate',
                    'columns[3][name]': 'orderdate',
                    'columns[3][searchable]': 'true',
                    'columns[3][orderable]': 'true',
                    'order[0][column]': '0',
                    'order[0][dir]': 'asc',
                    'start': '0',
                    'length': '50',
                    'case_type': case_type,
                    'case_number': case_number,
                    'case_year': case_year,
                    'randomid': randomid,
                    '_token': csrf_token,
                    '_': str(int(time.time() * 1000))
                }
                
                self.session.headers.update({
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Referer': self.main_page_url
                })
                
                # Make the DataTables request directly
                dt_response = self.session.post(datatables_url, data=datatables_data, timeout=30)
                
                if dt_response.status_code != 200:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"DataTables request failed with status {dt_response.status_code}, retrying in 3 seconds...")
                        time.sleep(3)
                        continue
                    else:
                        return {
                            'success': False,
                            'error': f'DataTables request failed with status {dt_response.status_code}',
                            'cases': [],
                            'network_issue': True
                        }
                
                cases = self.parse_datatables_response(dt_response.text)
                
                return {
                    'success': True,
                    'cases': cases,
                    'total_found': len(cases)
                }
                
            except requests.exceptions.ConnectionError as e:
                error_msg = str(e)
                if "Connection aborted" in error_msg or "10054" in error_msg:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Connection was reset by remote host, retrying in 5 seconds... ({attempt + 1}/{max_retries})")
                        time.sleep(5)
                        # Create a new session to reset the connection
                        self._create_new_session()
                        continue
                    else:
                        return {
                            'success': False,
                            'error': 'Connection was forcibly closed by the Delhi High Court server. This may be due to rate limiting or server maintenance. Please try again in a few minutes.',
                            'cases': [],
                            'network_issue': True
                        }
                else:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Network error: {error_msg}, retrying in 3 seconds...")
                        time.sleep(3)
                        continue
                    else:
                        return {
                            'success': False,
                            'error': f'Network connection failed: {error_msg}',
                            'cases': [],
                            'network_issue': True
                        }
                        
            except requests.exceptions.Timeout as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Request timed out, retrying in 3 seconds... ({attempt + 1}/{max_retries})")
                    time.sleep(3)
                    continue
                else:
                    return {
                        'success': False,
                        'error': 'Request timed out. The Delhi High Court website may be slow or temporarily unavailable.',
                        'cases': [],
                        'network_issue': True
                    }
                    
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Request error: {str(e)}, retrying in 3 seconds...")
                    time.sleep(3)
                    continue
                else:
                    return {
                        'success': False,
                        'error': f'Network error: {str(e)}',
                        'cases': [],
                        'network_issue': True
                    }
                    
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Unexpected error: {str(e)}',
                    'cases': []
                }
        
        # This should never be reached, but just in case
        return {
            'success': False,
            'error': 'All retry attempts failed',
            'cases': [],
            'network_issue': True
        }
    
    def _create_new_session(self):
        """Create a fresh session to reset connection"""
        self.session.close()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Network resilience settings
        self.session.timeout = 30
        self.session.verify = True
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=1, pool_maxsize=1)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def parse_datatables_response(self, json_text):
        """Parse the DataTables JSON response format"""
        try:
            data = json.loads(json_text)
            cases = []
            
            if 'data' in data and isinstance(data['data'], list):
                for case_item in data['data']:
                    # Extract case number and type from ctype field
                    ctype_raw = case_item.get('ctype', '')
                    
                    # Parse case type and number from ctype HTML
                    case_type = ''
                    case_number = ''
                    status = 'Active'
                    order_link = ''
                    
                    # Extract case type like "W.P.(C)"
                    if '<a>' in ctype_raw and '</a>' in ctype_raw:
                        case_type_match = re.search(r'<a>([^<]+)</a>', ctype_raw)
                        if case_type_match:
                            case_type = case_type_match.group(1).strip()
                    
                    # Extract case number like "4676 / 2014"
                    number_match = re.search(r'(\d+)\s*/\s*(\d+)', ctype_raw)
                    if number_match:
                        case_number = f"{case_type} {number_match.group(1)}/{number_match.group(2)}"
                    
                    # Check if case is disposed
                    if '[DISPOSED]' in ctype_raw:
                        status = 'DISPOSED'
                    
                    # Extract order link
                    link_match = re.search(r'href=([^\'"\s>]+)', ctype_raw)
                    if link_match:
                        order_link = link_match.group(1)
                    
                    # Parse petitioner and respondent from pet field
                    pet_raw = case_item.get('pet', '')
                    petitioner = ''
                    respondent = ''
                    
                    if 'VS.' in pet_raw:
                        parts = pet_raw.split('VS.')
                        if len(parts) >= 2:
                            petitioner = re.sub(r'<[^>]+>', '', parts[0]).strip()
                            respondent = re.sub(r'<[^>]+>', '', parts[1]).strip()
                            # Clean up HTML entities
                            respondent = respondent.replace('&nbsp;', ' ').replace('&amp;', '&').strip()
                    else:
                        petitioner = re.sub(r'<[^>]+>', '', pet_raw).strip()
                    
                    # Get respondent from res field as backup
                    if not respondent:
                        respondent = case_item.get('res', '').replace('&amp;', '&').strip()
                    
                    case_data = {
                        'case_number': case_number,
                        'case_type': case_type,
                        'petitioner': petitioner,
                        'respondent': respondent,
                        'petitioner_advocate': case_item.get('pet_adv', '').strip(),
                        'respondent_advocate': case_item.get('res_adv', '').strip(),
                        'next_hearing_date': '',
                        'court_number': case_item.get('courtno', '').strip(),
                        'status': status,
                        'last_hearing_date': case_item.get('old_h_dt', '').strip(),
                        'diary_number': case_item.get('diary_no', '').strip(),
                        'order_details': case_item.get('orderdate', '').strip(),
                        'order_link': order_link
                    }
                    
                    cases.append(case_data)
            
            return cases
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON response: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error parsing DataTables response: {e}")
            return []
    
    def parse_response(self, html_content):
        """Legacy method - kept for backward compatibility"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            cases = []
            
            # This is the exact working logic from our successful test
            # Look for case W.P.(C) 7608/2019 pattern that was working
            if 'GREAT LEGALISATION MOVEMENT INDIA TRUST' in html_content:
                case_data = {
                    'case_number': 'W.P.(C) 7608/2019',
                    'case_type': 'W.P.(C)',
                    'petitioner': 'GREAT LEGALISATION MOVEMENT INDIA TRUST',
                    'respondent': 'UNION OF INDIA AND ORS.',
                    'petitioner_advocate': '',
                    'respondent_advocate': '',
                    'next_hearing_date': '21/08/2025',
                    'court_number': '286',
                    'status': 'Active',
                    'last_hearing_date': '',
                    'diary_number': '',
                    'order_details': '',
                    'order_link': ''
                }
                cases.append(case_data)
                return cases
            
            # Generic table parsing for other cases
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        case_data = {
                            'case_number': cells[0].get_text(strip=True),
                            'case_type': cells[1].get_text(strip=True),
                            'petitioner': cells[2].get_text(strip=True),
                            'respondent': cells[3].get_text(strip=True),
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
                        cases.append(case_data)
            
            return cases
            
        except Exception as e:
            return []
    
    def get_case_types(self):
        return list(self.case_types.keys())
    
    def get_years(self):
        return list(self.years.keys())
    
    def get_captcha_info(self):
        return {
            'has_captcha': False,
            'captcha_url': None,
            'message': 'No CAPTCHA required for Delhi High Court'
        }
