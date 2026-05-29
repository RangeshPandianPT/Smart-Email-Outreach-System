import pytest
from datetime import datetime, timedelta
from src.core.database import get_db_connection

# A simple test to verify database queries for scheduler 
def test_followup_logic_query():
    # The database is already isolated via the autouse fixture in conftest.py
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Insert a mock lead that should receive a followup
        cursor.execute('''
            INSERT INTO leads (name, email, status, email_sent_timestamp, followup_count)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Followup Test', 'followup@test.com', 'Sent', (datetime.utcnow() - timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'), 0))
        
        # Insert a mock lead that should NOT receive a followup yet
        cursor.execute('''
            INSERT INTO leads (name, email, status, email_sent_timestamp, followup_count)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Too Soon Test', 'toosoon@test.com', 'Sent', (datetime.utcnow() - timedelta(hours=10)).strftime('%Y-%m-%d %H:%M:%S'), 0))
        
        conn.commit()

        # Execute the query logic that process_followups uses
        cursor.execute("SELECT * FROM leads WHERE status = 'Sent' AND followup_count < 2 AND email_sent_timestamp IS NOT NULL")
        leads = cursor.fetchall()
        
        candidates_for_followup = []
        for lead in leads:
            last_action_str = lead['last_followup_timestamp'] or lead['email_sent_timestamp']
            delay_hours = 48 if lead['followup_count'] == 0 else 96
            last_action = datetime.strptime(last_action_str, '%Y-%m-%d %H:%M:%S')
            diff_hours = (datetime.utcnow() - last_action).total_seconds() / 3600
            
            if diff_hours >= delay_hours:
                candidates_for_followup.append(lead['email'])

        assert 'followup@test.com' in candidates_for_followup
        assert 'toosoon@test.com' not in candidates_for_followup
