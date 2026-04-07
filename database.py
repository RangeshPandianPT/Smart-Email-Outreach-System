import sqlite3
import os
from contextlib import contextmanager

DB_FILE = "crm.db"

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Leads table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            role TEXT,
            company TEXT,
            email TEXT UNIQUE,
            service_needed TEXT,
            status TEXT DEFAULT 'Pending',  -- Pending, Generated, Sent, Replied, Bounced
            deal_stage TEXT DEFAULT 'Cold', -- Cold, Interested, Meeting Request, Not Interested, Neutral
            thread_id TEXT,                 -- To link replies from Gmail
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Email content table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lead_id INTEGER,
            subject TEXT,
            body TEXT,
            sent_at TIMESTAMP,
            message_id TEXT,
            FOREIGN KEY(lead_id) REFERENCES leads(id)
        )
        ''')
        
init_db()
