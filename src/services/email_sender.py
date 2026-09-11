import base64
import time
import random
from datetime import datetime, date
from email.message import EmailMessage
from sqlalchemy import func
from src.services.gmail_client import get_gmail_service
from src.core.database import SessionLocal
from src.core.models import Lead, EmailLog
from src.core.config import settings
from src.services.email_generator import generate_followup_email
from src.core.logger import setup_logger
from src.services.rate_limiter import RateLimiter

logger = setup_logger("email_sender")

def _emails_sent_today(db) -> int:
    today = date.today()
    count = db.query(func.count(Lead.id)).filter(
        Lead.email_sent_timestamp != None,
        func.date(Lead.email_sent_timestamp) == today
    ).scalar()
    return count or 0

def _can_send_more_today(db) -> bool:
    return _emails_sent_today(db) < settings.MAX_EMAILS_PER_DAY

@RateLimiter(max_calls=settings.RATE_LIMIT_PER_HOUR, period_seconds=3600)
@RateLimiter(max_calls=settings.RATE_LIMIT_PER_MINUTE, period_seconds=60)
@RateLimiter(max_calls=1, period_seconds=1.0/settings.RATE_LIMIT_PER_SECOND)
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
            logger.warning(
                f"Send attempt {attempt}/{max_attempts} failed: {type(e).__name__}: {e}. "
                f"Retrying in {backoff_seconds:.1f}s..."
            )
            time.sleep(backoff_seconds)

    raise last_error

def create_message(to_email, subject, body_text, previous_message_id=None, thread_id=None):
    message = EmailMessage()
    message.set_content(body_text)
    message['To'] = to_email
    message['Subject'] = subject
    
    if previous_message_id:
        message['In-Reply-To'] = previous_message_id
        message['References'] = previous_message_id

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    payload = {'raw': encoded_message}
    if thread_id:
        payload['threadId'] = thread_id
    return payload

def send_email_to_lead(lead_id: int):
    try:
        service = get_gmail_service()
    except Exception as e:
        logger.error(f"Failed to initialize Gmail service for lead {lead_id}: {type(e).__name__}: {e}")
        return False

    db = SessionLocal()
    try:
        if not _can_send_more_today(db):
            limit_msg = (
                f"Daily send limit reached ({settings.MAX_EMAILS_PER_DAY}). "
                f"Lead {lead_id} will remain queued."
            )
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                lead.last_send_error = limit_msg
                lead.last_send_attempt_timestamp = datetime.utcnow()
                db.commit()
            logger.warning(limit_msg)
            return False

        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if not lead:
            logger.info(f"Lead {lead_id} not found.")
            return False

        if lead.status in ('Sent', 'Replied'):
            logger.info(f"Lead {lead_id} already processed.")
            return False

        draft = db.query(EmailLog).filter(EmailLog.lead_id == lead_id).order_by(EmailLog.id.desc()).first()
        if not draft:
            logger.info(f"No draft found for lead {lead_id}.")
            return False

        try:
            lead.send_attempts = (lead.send_attempts or 0) + 1
            lead.last_send_attempt_timestamp = datetime.utcnow()
            db.commit()

            msg = create_message(lead.email, draft.subject, draft.body)

            sent_message = _send_with_retry(service, msg, max_attempts=3)
            message_id = sent_message['id']
            thread_id = sent_message.get('threadId')

            lead.status = 'Sent'
            lead.thread_id = thread_id
            lead.email_sent_timestamp = datetime.utcnow()
            lead.last_send_error = None
            
            draft.sent_at = datetime.utcnow()
            draft.message_id = message_id
            
            db.commit()

            logger.info(f"Sent email to {lead.email}. Thread ID: {thread_id}")
            return True

        except Exception as e:
            lead.last_send_error = f"{type(e).__name__}: {e}"[:500]
            db.commit()
            logger.error(f"Failed to send to {lead.email}: {type(e).__name__}: {e}")
            return False
    finally:
        db.close()

def process_email_queue_db():
    db = SessionLocal()
    try:
        pending_leads = db.query(Lead).join(EmailLog).filter(
            Lead.status == 'Approved',
            EmailLog.sent_at == None
        ).distinct().all()

        if not _can_send_more_today(db):
            logger.warning(f"Daily send limit reached ({settings.MAX_EMAILS_PER_DAY}). Queue processing skipped.")
            return

        if not pending_leads:
            logger.info("No pending drafted emails in queue.")
            return

        logger.info(f"Processing email queue for {len(pending_leads)} lead(s).")
        
        # Store IDs since the session state could change inside the loop or across threads
        lead_ids = [l.id for l in pending_leads]
    finally:
        db.close()

    for lead_id in lead_ids:
        db = SessionLocal()
        try:
            if not _can_send_more_today(db):
                print(f"Daily send limit reached ({settings.MAX_EMAILS_PER_DAY}). Stopping queue.")
                break
        finally:
            db.close()

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
    db = SessionLocal()
    try:
        leads = db.query(Lead).filter(
            Lead.status == 'Sent',
            Lead.followup_count < 2,
            Lead.email_sent_timestamp != None
        ).all()
        
        for lead in leads:
            now = datetime.utcnow()
            last_action = lead.last_followup_timestamp or lead.email_sent_timestamp
            
            delay_hours = 48 if lead.followup_count == 0 else 96
            
            try:
                diff_hours = (now - last_action).total_seconds() / 3600
                if diff_hours >= delay_hours:
                    print(f"Triggering follow-up {lead.followup_count + 1} for {lead.email}")
                    
                    prev_log = db.query(EmailLog).filter(EmailLog.lead_id == lead.id).order_by(EmailLog.id.desc()).first()
                    if not prev_log:
                        print(f"No previous email log found for lead {lead.id}. Skipping follow-up.")
                        continue
                        
                    # Prepare dict for followup generator
                    lead_dict = {
                        "name": lead.name, "company": lead.company, "role": lead.role
                    }
                    body = generate_followup_email(lead_dict, prev_log.body, lead.followup_count + 1)
                    
                    service = get_gmail_service()
                    msg = create_message(
                        to_email=lead.email, 
                        subject=prev_log.subject, 
                        body_text=body,
                        previous_message_id=prev_log.message_id,
                        thread_id=lead.thread_id
                    )
                    
                    sent_msg = service.users().messages().send(userId='me', body=msg).execute()
                    
                    lead.followup_count += 1
                    lead.last_followup_timestamp = datetime.utcnow()
                    
                    new_log = EmailLog(
                        lead_id=lead.id,
                        subject=prev_log.subject,
                        body=body,
                        sent_at=datetime.utcnow(),
                        message_id=sent_msg['id']
                    )
                    db.add(new_log)
                    db.commit()
            except Exception as e:
                print(f"Error processing follow-up for lead {lead.id}: {e}")
    finally:
        db.close()
