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

        # Campaigns table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'Active',  -- Active, Paused, Archived
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Leads table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
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
            last_message_id TEXT,
            FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
        )
        ''')

        # Add campaign_id column to existing table safely
        try:
            cursor.execute("ALTER TABLE leads ADD COLUMN campaign_id INTEGER")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add new columns to existing table safely 
        for col in [
            "reply_text TEXT",
            "reply_status TEXT",
            "reply_timestamp TIMESTAMP",
            "last_message_id TEXT",
            "email_sent_timestamp TIMESTAMP",
            "followup_count INTEGER DEFAULT 0",
            "last_followup_timestamp TIMESTAMP",
            "send_attempts INTEGER DEFAULT 0",
            "last_send_attempt_timestamp TIMESTAMP",
            "last_send_error TEXT",
        ]:
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

        # Tracks Gmail message processing to prevent duplicate handling across restarts.
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS inbox_processed_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE,
            sender_email TEXT,
            lead_id INTEGER,
            status TEXT NOT NULL,             -- processed, ignored, failed
            error TEXT,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(lead_id) REFERENCES leads(id)
        )
        ''')

        # Migration tracking for future use
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
init_db()
