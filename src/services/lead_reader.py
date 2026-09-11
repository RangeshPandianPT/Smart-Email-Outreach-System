import pandas as pd
import re
from src.core.database import SessionLocal
from src.core.models import Lead

def is_valid_email(email: str) -> bool:
    """
    Validates email using regex (syntax check only — no DNS lookup).
    """
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))

def import_leads_from_csv(csv_path: str):
    """
    Reads leads from a CSV file and inserts them into the database.
    Skips invalid emails and duplicates.
    """
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
        return 0

    inserted_count = 0
    db = SessionLocal()
    try:
        for _, row in df.iterrows():
            email = str(row.get('Email', '')).strip()

            if not is_valid_email(email):
                print(f"Skipped invalid email: {email}")
                continue

            name = str(row.get('Name', '')).strip()
            role = str(row.get('Role', '')).strip()
            company = str(row.get('Company', '')).strip()
            service_needed = str(row.get('Service Needed', '')).strip()

            existing = db.query(Lead).filter(Lead.email == email).first()
            if not existing:
                try:
                    lead = Lead(
                        name=name, 
                        role=role, 
                        company=company, 
                        email=email, 
                        service_needed=service_needed, 
                        status='Pending', 
                        deal_stage='Cold'
                    )
                    db.add(lead)
                    inserted_count += 1
                except Exception as e:
                    print(f"Failed to insert {email}: {e}")
        db.commit()
    except Exception as e:
        print(f"Failed during import: {e}")
        db.rollback()
    finally:
        db.close()
        
    print(f"Imported {inserted_count} new leads from {csv_path}")
    return inserted_count

if __name__ == "__main__":
    count = import_leads_from_csv("sample_leads.csv")
    print(f"Successfully imported {count} leads.")
