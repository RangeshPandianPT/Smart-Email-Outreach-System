import base64
import time
import random
from email.message import EmailMessage
from gmail_client import get_gmail_service
from database import get_db_connection
from config import settings

def create_message(to_email, subject, body_text):
    message = EmailMessage()
    message.set_content(body_text)
    message['To'] = to_email
    message['From'] = settings.SMTP_USER # Should be the authenticated Gmail account
    message['Subject'] = subject
    
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': encoded_message}

def send_email_to_lead(lead_id: int):
    """
    Retrieves the lead from Db, generates subject and body (if not generated), 
    and sends via Gmail API. Updates DB with status and thread_id.
    """
    service = get_gmail_service()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        lead = cursor.fetchone()
        
        if not lead:
            print(f"Lead {lead_id} not found.")
            return False
            
        if lead['status'] in ('Sent', 'Replied'):
            print(f"Lead {lead_id} already processed.")
            return False
            
        # We assume email_generator has populated the DB, but to keep concerns separated,
        # we pull from email_logs if we drafted it there.
        # For simplicity, we'll fetch the drafted email from email_logs
        cursor.execute("SELECT * FROM email_logs WHERE lead_id = ? ORDER BY id DESC LIMIT 1", (lead_id,))
        draft = cursor.fetchone()
        
        if not draft:
            print(f"No draft found for lead {lead_id}.")
            return False
            
        try:
            # Create Gmail message
            body = draft['body']
            subject = draft['subject']
            to_email = lead['email']
            
            msg = create_message(to_email, subject, body)
            
            # Send message
            sent_message = service.users().messages().send(userId='me', body=msg).execute()
            message_id = sent_message['id']
            thread_id = sent_message['threadId']
            
            # Update DB
            cursor.execute("""
                UPDATE leads 
                SET status = 'Sent', thread_id = ?, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (thread_id, lead_id))
            
            cursor.execute("""
                UPDATE email_logs
                SET sent_at = CURRENT_TIMESTAMP, message_id = ?
                WHERE id = ?
            """, (message_id, draft['id']))
            
            print(f"Sent email to {to_email}. Thread ID: {thread_id}")
            return True
            
        except Exception as e:
            print(f"Failed to send to {lead['email']}: {e}")
            return False

def process_email_queue():
    """
    Finds leads with status 'Drafted', sends them one by one, with delays.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Find all leads that have an email log but are not 'Sent'
        cursor.execute("""
            SELECT l.id 
            FROM leads l
            JOIN email_logs el ON l.id = el.lead_id
            WHERE l.status = 'Drafted' OR l.status = 'Pending' AND el.sent_at IS NULL
        """)
        pending_leads = cursor.fetchall()
        
    for row in pending_leads:
        lead_id = row['id']
        success = send_email_to_lead(lead_id)
        if success:
            delay = random.randint(settings.MIN_DELAY_SECONDS, settings.MAX_DELAY_SECONDS)
            print(f"Sleeping for {delay} seconds before next email...")
            time.sleep(delay)
