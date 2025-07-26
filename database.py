import sqlite3
import os
from datetime import datetime

# Database file location
DATABASE = 'instance/orb.db'

def init_database():
    """Initialize the database and create tables if they don't exist"""
    # Create instance directory if it doesn't exist
    os.makedirs('instance', exist_ok=True)
    
    # Connect to database (creates file if doesn't exist)
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create submissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text_content TEXT,
            doodle_filename TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            submission_type TEXT CHECK(submission_type IN ('text', 'doodle', 'both'))
        )
    ''')
    
    conn.commit()
    conn.close()

def add_submission(text_content=None, doodle_filename=None):
    """Add a new submission to the database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Determine submission type
    if text_content and doodle_filename:
        submission_type = 'both'
    elif text_content:
        submission_type = 'text'
    elif doodle_filename:
        submission_type = 'doodle'
    else:
        return None  # Invalid submission
    
    cursor.execute('''
        INSERT INTO submissions (text_content, doodle_filename, submission_type)
        VALUES (?, ?, ?)
    ''', (text_content, doodle_filename, submission_type))
    
    submission_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return submission_id

def get_random_submission():
    """Get a random submission from the database"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, text_content, doodle_filename, submission_type, timestamp
        FROM submissions
        ORDER BY RANDOM()
        LIMIT 1
    ''')
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {
            'id': result[0],
            'text_content': result[1],
            'doodle_filename': result[2],
            'submission_type': result[3],
            'timestamp': result[4]
        }
    return None

def get_submission_count():
    """Get total number of submissions"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM submissions')
    count = cursor.fetchone()[0]
    
    conn.close()
    return count

# Initialize database when this file is imported
if __name__ == '__main__':
    init_database()
    print("Database initialized successfully!")