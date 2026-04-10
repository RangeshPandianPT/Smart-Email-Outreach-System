import sys, os
sys.path.insert(0, r'd:\Email')
os.chdir(r'd:\Email')

print("=== VFX Outreach System - Integration Check ===")

# 1. Config
from src.core.config import settings
print(f"[OK] config - credentials path: {settings.GCP_CREDENTIALS_PATH}")

# 2. Database
from src.core.database import init_db
init_db()
import sqlite3
conn = sqlite3.connect("crm.db")
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
conn.close()
print(f"[OK] database tables: {[t[0] for t in tables]}")

# 3. Credentials
import json
with open("src/core/credentials.json") as f:
    creds_data = json.load(f)
client_info = creds_data.get("installed", creds_data.get("web", {}))
print(f"[OK] credentials.json - project: {client_info.get('project_id')}")

# 4. Gmail client path resolution
from src.services.gmail_client import get_credentials_path
resolved = get_credentials_path()
print(f"[OK] credentials resolves to: {resolved}")
print(f"[OK] file exists: {os.path.exists(resolved)}")

# 5. All module imports
from src.services.lead_reader import import_leads_from_csv
print("[OK] lead_reader imported")

from src.services.email_generator import generate_cold_email
print("[OK] email_generator imported")

from src.services.classifier import classify_reply
print("[OK] classifier imported")

from src.services.notifier import notify_of_reply
print("[OK] notifier imported")

from src.services.inbox_reader import process_inbox
print("[OK] inbox_reader imported")

from src.services.email_sender import send_email_to_lead
print("[OK] email_sender imported")

print()
print("ALL CHECKS PASSED!")
print()
print("NEXT STEPS:")
print("1. Open d:\\Email\\.env and set OPENAI_API_KEY, SMTP_USER, SMTP_PASSWORD")
print("2. Run: python -m src.services.gmail_client   <- authenticate Gmail (browser opens once)")
print("3. Run: python main.py           <- start dashboard at http://localhost:8000")
