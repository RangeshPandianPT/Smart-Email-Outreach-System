from src.core.database import get_db_connection
from src.services.analytics import generate_insights, get_analytics_data


def _insert_lead(status, reply_status=None, email_sent_timestamp=None, reply_timestamp=None):
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
                "Lead",
                "Producer",
                "Studio",
                f"{status.lower()}-{reply_status or 'none'}-{email_sent_timestamp or 'na'}@example.com",
                "VFX",
                status,
                reply_status or "Cold",
                reply_status,
                email_sent_timestamp,
                reply_timestamp,
            ),
        )


def test_get_analytics_data_calculates_conversion_and_response_time():
    _insert_lead("Sent", email_sent_timestamp="2026-01-01 10:00:00")
    _insert_lead(
        "Replied",
        reply_status="Interested",
        email_sent_timestamp="2026-01-01 09:00:00",
        reply_timestamp="2026-01-01 15:00:00",
    )
    _insert_lead(
        "Replied",
        reply_status="Not Interested",
        email_sent_timestamp="2026-01-01 11:00:00",
        reply_timestamp="2026-01-02 11:00:00",
    )

    data = get_analytics_data()

    assert data["total_sent"] == 3
    assert data["total_replies"] == 2
    assert data["interested"] == 1
    assert data["not_interested"] == 1
    assert data["meeting_requests"] == 0
    assert data["conversion_rate"] == 33.33
    assert data["avg_response_time_hours"] == 15.0


def test_generate_insights_handles_no_sends():
    insights = generate_insights(
        {
            "total_sent": 0,
            "total_replies": 0,
            "interested": 0,
            "not_interested": 0,
            "meeting_requests": 0,
            "conversion_rate": 0.0,
            "avg_response_time_hours": 0.0,
        }
    )

    assert insights == ["No emails sent yet to analyze."]
