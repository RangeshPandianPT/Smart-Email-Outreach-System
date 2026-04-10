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
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reply_text TEXT,
            reply_status TEXT,
            reply_timestamp TIMESTAMP,
            last_message_id TEXT
        )
        ''')

        # Add new columns to existing table safely 
        for col in ["reply_text TEXT", "reply_status TEXT", "reply_timestamp TIMESTAMP", "last_message_id TEXT", "email_sent_timestamp TIMESTAMP", "followup_count INTEGER DEFAULT 0", "last_followup_timestamp TIMESTAMP"]:
            try:
                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass # Column already exists

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
