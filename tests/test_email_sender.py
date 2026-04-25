from src.core.database import get_db_connection
from src.services import email_sender


class _ExecResult:
    def __init__(self, payload):
        self._payload = payload

    def execute(self):
        return self._payload


class _FakeMessagesApi:
    def __init__(self):
        self.sent_payloads = []

    def send(self, userId, body):
        self.sent_payloads.append({"userId": userId, "body": body})
        return _ExecResult({"id": "msg-1", "threadId": "thread-1"})


class _FakeUsersApi:
    def __init__(self):
        self._messages_api = _FakeMessagesApi()

    def messages(self):
        return self._messages_api


class _FakeGmailService:
    def __init__(self):
        self._users_api = _FakeUsersApi()

    def users(self):
        return self._users_api


def _insert_lead_with_draft(email: str = "alice@example.com"):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO leads (name, role, company, email, service_needed, status, deal_stage)
            VALUES (?, ?, ?, ?, ?, 'Drafted', 'Cold')
            """,
            ("Alice", "Producer", "Studio A", email, "CGI"),
        )
        lead_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO email_logs (lead_id, subject, body) VALUES (?, ?, ?)",
            (lead_id, "Subject", "Email body"),
        )
    return lead_id


def test_send_email_to_lead_marks_lead_sent(monkeypatch):
    lead_id = _insert_lead_with_draft()
    fake_service = _FakeGmailService()
    monkeypatch.setattr(email_sender, "get_gmail_service", lambda: fake_service)

    assert email_sender.send_email_to_lead(lead_id) is True

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT status, thread_id, email_sent_timestamp, last_send_error, send_attempts
            FROM leads
            WHERE id = ?
            """,
            (lead_id,),
        )
        lead = cursor.fetchone()

        cursor.execute(
            "SELECT sent_at, message_id FROM email_logs WHERE lead_id = ? ORDER BY id DESC LIMIT 1",
            (lead_id,),
        )
        draft = cursor.fetchone()

    assert lead["status"] == "Sent"
    assert lead["thread_id"] == "thread-1"
    assert lead["email_sent_timestamp"] is not None
    assert lead["last_send_error"] is None
    assert lead["send_attempts"] == 1
    assert draft["sent_at"] is not None
    assert draft["message_id"] == "msg-1"
    assert len(fake_service.users().messages().sent_payloads) == 1


def test_process_email_queue_calls_sender_for_pending_drafts(monkeypatch):
    lead_ids = [
        _insert_lead_with_draft("alice1@example.com"),
        _insert_lead_with_draft("alice2@example.com"),
    ]
    called_ids = []

    def _fake_send(lead_id):
        called_ids.append(lead_id)
        return True

    monkeypatch.setattr(email_sender, "send_email_to_lead", _fake_send)
    monkeypatch.setattr(email_sender.time, "sleep", lambda *_args, **_kwargs: None)

    email_sender.process_email_queue()

    assert sorted(called_ids) == sorted(lead_ids)
