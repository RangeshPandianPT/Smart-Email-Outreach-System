import base64
import binascii
import time
from bs4 import BeautifulSoup
from src.services.gmail_client import get_gmail_service
from src.core.database import get_db_connection
from src.services.classifier import classify_reply

PROCESSED = "processed"
IGNORED = "ignored"
FAILED = "failed"


def _extract_sender_email(headers) -> str:
    for header in headers:
        if header.get('name', '').lower() == 'from':
            sender_raw = header.get('value', '')
            if '<' in sender_raw and '>' in sender_raw:
                return sender_raw.split('<')[1].split('>')[0].strip()
            return sender_raw.strip()
    return ""


def _decode_body_data(body_data: str) -> str:
    if not body_data:
        return ""

    padded = body_data + '=' * (-len(body_data) % 4)
    try:
        return base64.urlsafe_b64decode(padded).decode('utf-8', errors='ignore')
    except (binascii.Error, ValueError):
        return ""


def _find_part_text(payload, target_mime_type: str) -> str:
    if payload.get('mimeType') == target_mime_type:
        data = payload.get('body', {}).get('data', "")
        decoded = _decode_body_data(data)
        if decoded:
            return decoded

    for part in payload.get('parts', []) or []:
        found = _find_part_text(part, target_mime_type)
        if found:
            return found

    return ""


def _extract_message_text(payload) -> str:
    plain_text = _find_part_text(payload, 'text/plain')
    if plain_text:
        return plain_text.strip()

    html_text = _find_part_text(payload, 'text/html')
    if html_text:
        return BeautifulSoup(html_text, "html.parser").get_text(" ", strip=True)

    root_body = payload.get('body', {}).get('data', "")
    fallback_text = _decode_body_data(root_body)
    return fallback_text.strip()


def _already_processed(cursor, msg_id: str) -> bool:
    cursor.execute(
        "SELECT status FROM inbox_processed_messages WHERE message_id = ?",
        (msg_id,),
    )
    row = cursor.fetchone()
    return bool(row and row['status'] == PROCESSED)


def _record_message_status(
    cursor,
    msg_id: str,
    sender_email: str | None,
    lead_id: int | None,
    status: str,
    error: str | None = None,
):
    error_value = (error or "")[:500] or None

    cursor.execute(
        "SELECT 1 FROM inbox_processed_messages WHERE message_id = ?",
        (msg_id,),
    )
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            """
            UPDATE inbox_processed_messages
            SET sender_email = ?,
                lead_id = ?,
                status = ?,
                error = ?,
                processed_at = CURRENT_TIMESTAMP
            WHERE message_id = ?
            """,
            (sender_email, lead_id, status, error_value, msg_id),
        )
    else:
        cursor.execute(
            """
            INSERT INTO inbox_processed_messages (message_id, sender_email, lead_id, status, error)
            VALUES (?, ?, ?, ?, ?)
            """,
            (msg_id, sender_email, lead_id, status, error_value),
        )

def process_inbox():
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
                msg_id = msg_ref.get('id')
                if not msg_id:
                    continue

                if _already_processed(cursor, msg_id):
                    continue

                msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()

                payload = msg.get('payload', {})
                headers = payload.get('headers', [])
                sender_email = _extract_sender_email(headers)

                if not sender_email:
                    _record_message_status(cursor, msg_id, None, None, IGNORED, "missing_sender")
                    continue

                cursor.execute("SELECT * FROM leads WHERE lower(email) = lower(?)", (sender_email,))
                lead = cursor.fetchone()

                if lead:
                    print(f"New reply detected from {sender_email}")
                    text_content = _extract_message_text(payload)

                    if not text_content:
                        _record_message_status(
                            cursor,
                            msg_id,
                            sender_email,
                            lead['id'],
                            FAILED,
                            "empty_or_undecodable_body",
                        )
                        continue

                    try:
                        classification = classify_reply(text_content)
                        print(f"Classified as {classification}")

                        cursor.execute('''
                            UPDATE leads
                            SET status = 'Replied',
                                deal_stage = ?,
                                reply_status = ?,
                                reply_text = ?,
                                reply_timestamp = CURRENT_TIMESTAMP,
                                last_message_id = ?,
                                last_updated = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (classification, classification, text_content, msg_id, lead['id']))

                        # Only mark message as read once it maps to a lead and processing succeeds.
                        service.users().messages().modify(
                            userId='me',
                            id=msg_id,
                            body={'removeLabelIds': ['UNREAD']},
                        ).execute()

                        _record_message_status(cursor, msg_id, sender_email, lead['id'], PROCESSED)
                        print('Database updated')
                        new_replies_count += 1
                    except Exception as e:
                        _record_message_status(
                            cursor,
                            msg_id,
                            sender_email,
                            lead['id'],
                            FAILED,
                            str(e),
                        )
                        print(f"Failed to process matched reply for {sender_email}: {e}")
                else:
                    # Keep unmatched unread emails untouched for manual triage.
                    _record_message_status(
                        cursor,
                        msg_id,
                        sender_email,
                        None,
                        IGNORED,
                        "sender_not_in_leads",
                    )

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
