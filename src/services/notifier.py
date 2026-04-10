import smtplib
from email.message import EmailMessage
from src.core.config import settings

def send_alert_email(subject: str, body: str):
    """
    Sends an internal alert email using standard SMTP.
    """
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("SMTP Credentials not configured. Skipping alert.")
        return

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = f"[VFX Outreach Alert] {subject}"
    msg['From'] = settings.SMTP_USER
    msg['To'] = settings.NOTIFICATION_EMAIL
    
    try:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Sent notification email: {subject}")
    except Exception as e:
        print(f"Failed to send alert email: {e}")

def notify_of_reply(lead_name: str, company: str, classification: str, text: str):
    subject = f"New {classification} reply from {lead_name} at {company}"
    body = f"""
We received a reply!

Lead: {lead_name}
Company: {company}
Classification: {classification}

Message Preview:
{text[:500]}...

Log into the CRM to view full details.
"""
    send_alert_email(subject, body)
