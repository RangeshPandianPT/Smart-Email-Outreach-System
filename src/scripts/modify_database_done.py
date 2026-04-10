import sys

with open(r'd:\Email\src\core\database.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add new columns to existing table safely
if 'email_sent_timestamp TIMESTAMP' not in text:
    old_cols = '# Add new columns to existing table safely\n        for col in ["reply_text TEXT", "reply_status TEXT", "reply_timestamp TIMESTAMP", "last_message_id TEXT"]:\n            try:\n                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col}")\n            except sqlite3.OperationalError:\n                pass # Column already exists'
    
    new_cols = '# Add new columns to existing table safely\n        for col in ["reply_text TEXT", "reply_status TEXT", "reply_timestamp TIMESTAMP", "last_message_id TEXT", "email_sent_timestamp TIMESTAMP", "followup_count INTEGER DEFAULT 0", "last_followup_timestamp TIMESTAMP"]:\n            try:\n                cursor.execute(f"ALTER TABLE leads ADD COLUMN {col}")\n            except sqlite3.OperationalError:\n                pass # Column already exists'
    text = text.replace(old_cols, new_cols)

with open(r'd:\Email\src\core\database.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Database Schema Updated!')
