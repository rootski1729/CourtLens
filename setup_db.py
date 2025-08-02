#!/usr/bin/env python3

import sqlite3
import os

def create_database():
    
    if os.path.exists('courtlens.db'):
        os.remove('courtlens.db')
        print("Removed old database")
    
    conn = sqlite3.connect('courtlens.db')
    cursor = conn.cursor()
    
    cursor.execute('''
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
            last_hearing_date TEXT,
            court_number TEXT,
            diary_number TEXT,
            order_details TEXT,
            order_link TEXT,
            search_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            raw_data TEXT  -- JSON string of complete case data
        )
    ''')
    
    # Create search_logs table
    cursor.execute('''
        CREATE TABLE search_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            search_params TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            results_count INTEGER DEFAULT 0,
            error_message TEXT,
            ip_address TEXT,
            user_agent TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('CREATE INDEX idx_cases_number ON cases(case_number)')
    cursor.execute('CREATE INDEX idx_cases_type ON cases(case_type)')
    cursor.execute('CREATE INDEX idx_cases_status ON cases(status)')
    cursor.execute('CREATE INDEX idx_search_logs_timestamp ON search_logs(timestamp)')
    
    conn.commit()
    conn.close()
    
    print("✅ Database created successfully!")
    print("Tables created: cases, search_logs")
    print("Indexes created for better performance")

if __name__ == "__main__":
    create_database()
