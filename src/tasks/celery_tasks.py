from src.core.celery_app import celery_app
from src.core.database import SessionLocal
from src.core.models import Lead, EmailLog
from src.services.email_generator import generate_cold_email, generate_subject_line
from src.services.email_sender import process_email_queue_db
import logging

logger = logging.getLogger(__name__)

@celery_app.task
def generate_all_pending_task():
    db = SessionLocal()
    try:
        pending_leads = db.query(Lead).filter(Lead.status == "Pending").all()
        for lead in pending_leads:
            # We convert model to dict if email_generator expects dicts
            lead_dict = {
                "id": lead.id, "name": lead.name, "role": lead.role, 
                "company": lead.company, "email": lead.email, 
                "service_needed": lead.service_needed,
                "status": lead.status, "deal_stage": lead.deal_stage
            }
            subject = generate_subject_line(lead_dict)
            body = generate_cold_email(lead_dict)
            
            if body and subject:
                email_log = EmailLog(lead_id=lead.id, subject=subject, body=body)
                db.add(email_log)
                lead.status = "Drafted"
                db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Error in generate_all_pending_task: {e}")
    finally:
        db.close()

@celery_app.task
def process_email_queue_task():
    # Will need to refactor email_sender.py to accept session
    process_email_queue_db()
