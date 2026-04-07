import pandas as pd
import time
import os
import traceback
from email.message import EmailMessage

# Importing existing tools so we don't duplicate logic.
from config import settings
from gmail_client import get_gmail_service
from email_generator import generate_cold_email, generate_subject_line

CSV_FILE = "sample_leads.csv"  # You can rename this to leads.csv if preferred
CHECK_INTERVAL_SECONDS = 60

def load_leads(csv_path: str) -> pd.DataFrame:
    """
    Loads leads from CSV safely. Handles missing 'Status' column gracefully.
    """
    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV file '{csv_path}' not found. Waiting for it to be created...")
        # Return an empty dataframe with expected columns
        return pd.DataFrame(columns=['Name', 'Role', 'Company', 'Email', 'Service Needed', 'Status'])

    import traceback
    try:
        # Try to use Pandas immediately.
        # This keeps the process fast while maintaining robustness.
        df = pd.read_csv(csv_path)

        # Ensure required 'Status' column exists before trying to read it
        if 'Status' not in df.columns:
            df['Status'] = 'Not Sent'
        else:
            df['Status'] = df['Status'].fillna('Not Sent')

        return df
    except Exception as e:
        print(f"[ERROR] Failed to read {csv_path}: {e}")
        return pd.DataFrame()

def update_csv(df: pd.DataFrame, csv_path: str):
    """
    Safely overwrites the CSV file with the updated DataFrame.
    """
    try:
        df.to_csv(csv_path, index=False)
    except Exception as e:
        print(f"[ERROR] Failed to save updates to {csv_path}: {e}")

def send_email(name: str, email: str, company: str, role: str, service_needed: str) -> bool:
    """
    Leverages existing AI generation and Gmail API to send the email.
    """
    service = get_gmail_service()
    
    # We construct a dict mimicking the DB row format expected by generate_code_email
    lead_dict = {
        "name": name,
        "company": company,
        "role": role,
        "email": email,
        "service_needed": service_needed
    }

    try:
        print(f"  -> Generating email content with AI for {name}...")
        subject = generate_subject_line(lead_dict)
        body = generate_cold_email(lead_dict)

        if not subject or not body:
            print(f"  [ERROR] AI generation failed for {email}.")
            return False

        # Construct raw email
        import base64
        message = EmailMessage()
        message.set_content(body)
        message['To'] = email
        message['From'] = settings.SMTP_USER 
        message['Subject'] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        raw_msg = {'raw': encoded_message}

        # Send using Gmail service
        sent_message = service.users().messages().send(userId='me', body=raw_msg).execute()
        print(f"  -> Email sent successfully! Message ID: {sent_message.get('id')}")
        return True

    except Exception as e:
        print(f"  [ERROR] Failed to send email to {email}: {e}")
        traceback.print_exc()
        return False

def process_leads(csv_path: str):
    """
    Processes the leads loaded from CSV.
    Only emails leads where Status == "Not Sent".
    Updates the status to "Sent" if successful.
    """
    df = load_leads(csv_path)
    
    if df.empty:
        return

    changes_made = False

    for index, row in df.iterrows():
        status = str(row.get('Status', '')).strip()
        email = str(row.get('Email', '')).strip()
        name = str(row.get('Name', 'Unknown')).strip()
        company = str(row.get('Company', 'Unknown')).strip()
        role = str(row.get('Role', 'Unknown')).strip()
        service = str(row.get('Service Needed', 'Unknown')).strip()

        if status == 'Sent':
            # Skip already processed
            # print(f"Skipping already processed lead: {name} ({company})")
            continue
            
        print(f"\nProcessing new lead: {name} ({company}) - {email}")

        # Send email
        success = send_email(name, email, company, role, service)

        # Update Status immediately
        if success:
            df.at[index, 'Status'] = 'Sent'
            changes_made = True
        else:
            print("  -> Keeping status as 'Not Sent' due to error.")

    if changes_made:
        print(f"\nUpdating {csv_path} with new statuses...")
        update_csv(df, csv_path)

def main_loop():
    """
    Continuous monitoring loop.
    Re-checks the CSV every 60-120 seconds.
    """
    print(f"Starting Smart CSV Detection System. Monitoring '{CSV_FILE}'...")
    while True:
        try:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Checking CSV for new leads...")
            process_leads(CSV_FILE)
            
        except Exception as e:
            print(f"[FATAL ERROR] Loop encountered an issue: {e}")
        
        print(f"Sleeping for {CHECK_INTERVAL_SECONDS} seconds...")
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main_loop()