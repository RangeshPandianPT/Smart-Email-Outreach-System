import base64
import time
from bs4 import BeautifulSoup
from src.services.gmail_client import get_gmail_service
from src.core.database import get_db_connection
from src.services.classifier import classify_reply

processed_message_ids = set()

def process_inbox():
    global processed_message_ids
    new_replies_count = 0
    service = get_gmail_service()

    try:
        results = service.users().messages().list(userId='me', q='is:unread').execute()
        messages = results.get('messages', [])

        if not messages:
            print('No new replies found')
            return 0

        with get_db_connection() as conn:
            cursor = conn.cursor()

            for msg_ref in messages:
                msg_id = msg_ref['id']

                if msg_id in processed_message_ids:
                    continue
                processed_message_ids.add(msg_id)

                msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()

                payload = msg.get('payload', {})
                headers = payload.get('headers', [])
                sender_email = ""
                for header in headers:
                    if header.get('name', '').lower() == 'from':
                        sender_raw = header.get('value', '')
                        if '<' in sender_raw and '>' in sender_raw:
                            sender_email = sender_raw.split('<')[1].split('>')[0].strip()
                        else:
                            sender_email = sender_raw.strip()
                        break

                if not sender_email:
                    continue

                cursor.execute("SELECT * FROM leads WHERE email = ?", (sender_email,))
                lead = cursor.fetchone()

                if lead:
                    print(f"New reply detected from {sender_email}")
                    body_data = ""
                    if 'parts' in payload:
                        for part in payload['parts']:
                            if part.get('mimeType') == 'text/plain':
                                body_data = part.get('body', {}).get('data', "")
                                break
                    elif 'body' in payload:
                        body_data = payload.get('body', {}).get('data', "")

                    if not body_data:
                        continue

                    try:
                        text_content = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        text_content = BeautifulSoup(text_content, "html.parser").get_text()
                    except Exception as e:
                        print("Failed to decode email body:", e)
                        continue

                    classification = classify_reply(text_content)
                    print(f"Classified as {classification}")

                    cursor.execute('''
                        UPDATE leads
                        SET status = 'Replied',
                            deal_stage = ?,
                            reply_status = ?,
                            reply_text = ?,
                            reply_timestamp = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (classification, classification, text_content, lead['id']))

                    print('Database updated')
                    new_replies_count += 1

                service.users().messages().modify(
                    userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}
                ).execute()

    except Exception as e:
        print(f'Error checking inbox: {e}')

    if new_replies_count > 0:
        print(f'New replies processed: {new_replies_count}')
        
    return new_replies_count

def run_background_reader():
    print("Starting Inbox Reader Background Worker...")
    while True:
        try:
            process_inbox()
        except Exception as e:
            print(f"[FATAL ERROR] Inbox reader loop encountered an issue: {e}")
        time.sleep(60)

if __name__ == "__main__":
    run_background_reader()
