from gmail_client import get_gmail_service
from database import get_db_connection
from classifier import classify_reply
from notifier import notify_of_reply
import base64
from bs4 import BeautifulSoup

def process_inbox():
    """
    Checks the inbox for unread messages. If a message is part of an ongoing thread,
    it classifies the reply, updates the DB, and fires a notification.
    """
    service = get_gmail_service()
    
    try:
        # Search for unread emails only
        results = service.users().messages().list(userId='me', q='is:unread').execute()
        messages = results.get('messages', [])
        
        if not messages:
            return
            
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            for msg_ref in messages:
                msg_id = msg_ref['id']
                
                # Fetch full message
                msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
                thread_id = msg['threadId']
                
                # Check if this thread belongs to a lead
                cursor.execute("SELECT * FROM leads WHERE thread_id = ?", (thread_id,))
                lead = cursor.fetchone()
                
                if lead:
                    # Extract body
                    payload = msg.get('payload', {})
                    body_data = ""
                    if 'parts' in payload:
                        for part in payload['parts']:
                            if part['mimeType'] == 'text/plain':
                                body_data = part['body'].get('data')
                                break
                    elif 'body' in payload:
                        body_data = payload['body'].get('data')
                        
                    if not body_data:
                        continue
                        
                    text_content = base64.urlsafe_b64decode(body_data).decode('utf-8')
                    
                    # Optional: Clean HTML if it's text/html but usually parts handles plain
                    text_content = BeautifulSoup(text_content, "html.parser").get_text()
                    
                    # Classify
                    classification = classify_reply(text_content)
                    
                    # Update lead status
                    cursor.execute("""
                        UPDATE leads 
                        SET status = 'Replied', deal_stage = ?, last_updated = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (classification, lead['id']))
                    
                    print(f"Lead {lead['name']} replied! Classified as: {classification}")
                    
                    # Notify
                    if classification in ['Interested', 'Meeting Request']:
                        notify_of_reply(lead['name'], lead['company'], classification, text_content)
                    
                    # Mark email as read so we don't process it again
                    service.users().messages().modify(
                        userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}
                    ).execute()
                    
    except Exception as e:
        print(f"Error checking inbox: {e}")
