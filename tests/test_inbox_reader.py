import base64

from src.core.database import get_db_connection
from src.services import inbox_reader


class _ExecResult:
    def __init__(self, payload):
        self._payload = payload

    def execute(self):
        return self._payload


class _FakeMessagesApi:
    def __init__(self, message_payload):
        self._message_payload = message_payload
        self.modified = []

    def list(self, userId, q):
        return _ExecResult({"messages": [{"id": "m1"}]})

    def get(self, userId, id, format):
        assert id == "m1"
        return _ExecResult(self._message_payload)

    def modify(self, userId, id, body):
        self.modified.append({"id": id, "body": body})
        return _ExecResult({})


class _FakeUsersApi:
    def __init__(self, message_payload):
        self._messages_api = _FakeMessagesApi(message_payload)

    def messages(self):
        return self._messages_api


class _FakeGmailService:
    def __init__(self, message_payload):
        self._users_api = _FakeUsersApi(message_payload)

    def users(self):
        return self._users_api


def _insert_sent_lead(email="reply@example.com"):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO leads (name, role, company, email, service_needed, status, deal_stage)
            VALUES (?, ?, ?, ?, ?, 'Sent', 'Cold')
            """,
            ("Lead Name", "Producer", "Studio A", email, "VFX"),
        )
        return cursor.lastrowid


def _message_payload_for_sender(sender_email, body_text):
    encoded_body = base64.urlsafe_b64encode(body_text.encode("utf-8")).decode("utf-8")
    return {
        "payload": {
            "headers": [{"name": "From", "value": f"Sender <{sender_email}>"}],
            "parts": [
                {
                    "mimeType": "text/plain",
                    "body": {"data": encoded_body},
                }
            ],
        }
    }


def test_process_inbox_updates_matched_lead(monkeypatch):
    lead_id = _insert_sent_lead("reply@example.com")
    payload = _message_payload_for_sender("reply@example.com", "Yes, we are interested. Let's schedule.")
    fake_service = _FakeGmailService(payload)

    monkeypatch.setattr(inbox_reader, "get_gmail_service", lambda: fake_service)
    monkeypatch.setattr(inbox_reader, "classify_reply", lambda _text: "Interested")

    processed_count = inbox_reader.process_inbox()
    assert processed_count == 1

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, deal_stage, reply_status, reply_text, last_message_id FROM leads WHERE id = ?",
            (lead_id,),
        )
        lead = cursor.fetchone()

        cursor.execute(
            "SELECT status, sender_email, lead_id FROM inbox_processed_messages WHERE message_id = 'm1'",
        )
        processed = cursor.fetchone()

    assert lead["status"] == "Replied"
    assert lead["deal_stage"] == "Interested"
    assert lead["reply_status"] == "Interested"
    assert "interested" in lead["reply_text"].lower()
    assert lead["last_message_id"] == "m1"

    assert processed["status"] == inbox_reader.PROCESSED
    assert processed["sender_email"] == "reply@example.com"
    assert processed["lead_id"] == lead_id

    modified_calls = fake_service.users().messages().modified
    assert len(modified_calls) == 1
    assert modified_calls[0]["id"] == "m1"
    assert modified_calls[0]["body"] == {"removeLabelIds": ["UNREAD"]}


def test_process_inbox_ignores_unmatched_sender(monkeypatch):
    payload = _message_payload_for_sender("unknown@example.com", "Please do not contact me.")
    fake_service = _FakeGmailService(payload)

    monkeypatch.setattr(inbox_reader, "get_gmail_service", lambda: fake_service)
    monkeypatch.setattr(inbox_reader, "classify_reply", lambda _text: "Not Interested")

    processed_count = inbox_reader.process_inbox()
    assert processed_count == 0

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, sender_email, error FROM inbox_processed_messages WHERE message_id = 'm1'",
        )
        tracked = cursor.fetchone()

    assert tracked["status"] == inbox_reader.IGNORED
    assert tracked["sender_email"] == "unknown@example.com"
    assert tracked["error"] == "sender_not_in_leads"
