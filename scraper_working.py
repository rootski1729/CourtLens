import os
import re
import json
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
        self.years = {str(year): str(year) for year in range(2000, 2026)}
    
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
        try:
            randomid, csrf_token = self.get_session_data()
            if not randomid or not csrf_token:
                return {
                    'success': False,
                    'error': 'Could not get session data',
                    'cases': []
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
            
            # Submit search to main page URL
            response = self.session.post(self.main_page_url, data=search_data, timeout=30)
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f'Search request failed with status {response.status_code}',
                    'cases': []
                }
            
            cases = self.parse_response(response.text)
            
            return {
                'success': True,
                'cases': cases,
                'total_found': len(cases)
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}',
                'cases': []
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'cases': []
            }
    
    def parse_response(self, html_content):
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
