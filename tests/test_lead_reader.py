from src.core.database import get_db_connection
from src.services.lead_reader import import_leads_from_csv, is_valid_email


def test_is_valid_email_accepts_common_formats():
    assert is_valid_email("alice@example.com")
    assert is_valid_email("a.b+tag@example.co.uk")
    assert not is_valid_email("invalid-email")
    assert not is_valid_email("missing-domain@")


def test_import_leads_from_csv_skips_invalid_and_duplicate(tmp_path):
    csv_path = tmp_path / "leads.csv"
    csv_path.write_text(
        "Name,Email,Role,Company,Service Needed\n"
        "Alice,alice@example.com,Producer,Studio A,CGI\n"
        "Bob,invalid-email,Director,Studio B,VFX\n"
        "Alice Duplicate,alice@example.com,Producer,Studio A,CGI\n"
        "Cara,cara@example.org,Head of Production,Studio C,Compositing\n",
        encoding="utf-8",
    )

    inserted = import_leads_from_csv(str(csv_path))
    assert inserted == 2

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT email, status, deal_stage FROM leads ORDER BY email")
        rows = cursor.fetchall()

    assert [row["email"] for row in rows] == ["alice@example.com", "cara@example.org"]
    assert all(row["status"] == "Pending" for row in rows)
    assert all(row["deal_stage"] == "Cold" for row in rows)
