import base64
import time
import random
from datetime import datetime
from email.message import EmailMessage
from src.services.gmail_client import get_gmail_service
from src.core.database import get_db_connection
from src.core.config import settings


def _emails_sent_today(cursor) -> int:
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM leads
        WHERE email_sent_timestamp IS NOT NULL
          AND date(email_sent_timestamp, 'localtime') = date('now', 'localtime')
        """
    )
    return cursor.fetchone()[0]


def _can_send_more_today(cursor) -> bool:
    return _emails_sent_today(cursor) < settings.MAX_EMAILS_PER_DAY


def _send_with_retry(service, msg, max_attempts: int = 3):
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return service.users().messages().send(userId='me', body=msg).execute()
        except Exception as e:
            last_error = e
            if attempt == max_attempts:
                break

            backoff_seconds = min(2 ** attempt, 20) + random.uniform(0.1, 0.9)
            print(
                f"Send attempt {attempt}/{max_attempts} failed: {type(e).__name__}: {e}. "
                f"Retrying in {backoff_seconds:.1f}s..."
            )
            time.sleep(backoff_seconds)

    raise last_error

def create_message(to_email, subject, body_text):
    message = EmailMessage()
    message.set_content(body_text)
    message['To'] = to_email
    # Let Gmail API use the authenticated account as sender to avoid From mismatch errors.
    message['Subject'] = subject

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {'raw': encoded_message}

def send_email_to_lead(lead_id: int):
    # Retrieves the lead from Db, generates subject and body (if not generated),      
    # and sends via Gmail API. Updates DB with status and thread_id.
    try:
        service = get_gmail_service()
    except Exception as e:
        print(f"Failed to initialize Gmail service for lead {lead_id}: {type(e).__name__}: {e}")
        return False

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if not _can_send_more_today(cursor):
            limit_msg = (
                f"Daily send limit reached ({settings.MAX_EMAILS_PER_DAY}). "
                f"Lead {lead_id} will remain queued."
            )
            cursor.execute(
                """
                UPDATE leads
                SET last_send_error = ?,
                    last_send_attempt_timestamp = CURRENT_TIMESTAMP,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (limit_msg, lead_id),
            )
            print(limit_msg)
            return False

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
            cursor.execute(
                """
                UPDATE leads
                SET send_attempts = COALESCE(send_attempts, 0) + 1,
                    last_send_attempt_timestamp = CURRENT_TIMESTAMP,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (lead_id,),
            )

            # Create Gmail message
            body = draft['body']
            subject = draft['subject']
            to_email = lead['email']

            msg = create_message(to_email, subject, body)

            # Send message with transient retry support.
            sent_message = _send_with_retry(service, msg, max_attempts=3)
            message_id = sent_message['id']
            thread_id = sent_message['threadId']

            # Update DB
            cursor.execute(
                """
                UPDATE leads
                SET status = 'Sent',
                    thread_id = ?,
                    last_updated = CURRENT_TIMESTAMP,
                    email_sent_timestamp = CURRENT_TIMESTAMP,
                    last_send_error = NULL
                WHERE id = ?
                """,
                (thread_id, lead_id),
            )

            cursor.execute("UPDATE email_logs SET sent_at = CURRENT_TIMESTAMP, message_id = ? WHERE id = ?", (message_id, draft['id']))

            print(f"Sent email to {to_email}. Thread ID: {thread_id}")
            return True

        except Exception as e:
            cursor.execute(
                """
                UPDATE leads
                SET last_send_error = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (f"{type(e).__name__}: {e}"[:500], lead_id),
            )
            print(f"Failed to send to {lead['email']}: {type(e).__name__}: {e}")
            return False

def process_email_queue():
    # Finds leads with status 'Drafted', sends them one by one, with delays.
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Find all leads that have an email log but are not 'Sent'
        cursor.execute("""
            SELECT DISTINCT l.id
            FROM leads l
            JOIN email_logs el ON l.id = el.lead_id
            WHERE l.status IN ('Drafted', 'Pending')
              AND el.sent_at IS NULL
        """)
        pending_leads = cursor.fetchall()

        if not _can_send_more_today(cursor):
            print(f"Daily send limit reached ({settings.MAX_EMAILS_PER_DAY}). Queue processing skipped.")
            return

    if not pending_leads:
        print("No pending drafted emails in queue.")
        return

    print(f"Processing email queue for {len(pending_leads)} lead(s).")

    for row in pending_leads:
        lead_id = row['id']

        # Re-check in each loop in case other jobs sent emails during this run.
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if not _can_send_more_today(cursor):
                print(f"Daily send limit reached ({settings.MAX_EMAILS_PER_DAY}). Stopping queue.")
                break

        try:
            success = send_email_to_lead(lead_id)
        except Exception as e:
            print(f"Unexpected queue error for lead {lead_id}: {type(e).__name__}: {e}")
            success = False

        if success:
            delay = random.randint(settings.MIN_DELAY_SECONDS, settings.MAX_DELAY_SECONDS)
            print(f"Sleeping for {delay} seconds before next email...")
            time.sleep(delay)

def process_followups():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, email_sent_timestamp, last_followup_timestamp, followup_count FROM leads WHERE status = 'Sent' AND followup_count < 2 AND email_sent_timestamp IS NOT NULL")
        
        leads = cursor.fetchall()
        for lead in leads:
            now = datetime.utcnow()
            last_action_str = lead['last_followup_timestamp'] or lead['email_sent_timestamp']
            try:
                last_action = datetime.strptime(last_action_str, '%Y-%m-%d %H:%M:%S')
                diff_hours = (now - last_action).total_seconds() / 3600
                if diff_hours >= 48:
                    print(f"Triggering follow-up for {lead['email']}")
                    subject = "Checking in"
                    body = "We wanted to follow up on our previous email.\n\nThanks!"
                    to_email = lead['email']
                    
                    service = get_gmail_service()
                    msg = create_message(to_email, subject, body)
                    
                    sent_msg = service.users().messages().send(userId='me', body=msg).execute()
                    
                    cursor.execute("UPDATE leads SET followup_count = followup_count + 1, last_followup_timestamp = CURRENT_TIMESTAMP WHERE id = ?", (lead['id'],))
                    cursor.execute("INSERT INTO email_logs (lead_id, subject, body, sent_at, message_id) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)", (lead['id'], subject, body, sent_msg['id']))
                    conn.commit()
            except Exception as e:
                print(f"Error processing follow-up for lead {lead['id']}: {e}")
