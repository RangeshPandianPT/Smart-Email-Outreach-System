from fastapi.testclient import TestClient

from main import app
from src.core.database import get_db_connection


client = TestClient(app)


def _insert_lead(name, status, reply_status=None, email_sent_timestamp=None, reply_timestamp=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO leads (
                name, role, company, email, service_needed, status, deal_stage,
                reply_status, email_sent_timestamp, reply_timestamp
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                "Producer",
                "Studio",
                f"{name.lower().replace(' ', '-')}-{status.lower()}@example.com",
                "VFX",
                status,
                "Cold",
                reply_status,
                email_sent_timestamp,
                reply_timestamp,
            ),
        )


def test_health_endpoint_returns_service_status():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_endpoint_returns_leads_and_analytics():
    _insert_lead("Ava", "Pending")
    _insert_lead(
        "Ben",
        "Replied",
        reply_status="Interested",
        email_sent_timestamp="2026-01-01 09:00:00",
        reply_timestamp="2026-01-01 15:00:00",
    )

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload["leads"]) == 2
    assert payload["summary"]["total_leads"] == 2
    assert payload["summary"]["pending_leads"] == 1
    assert payload["summary"]["replied_leads"] == 1
    assert payload["analytics"]["total_replies"] == 1
