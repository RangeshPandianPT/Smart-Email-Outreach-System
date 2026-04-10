import re
with open(r'd:\Email\src\services\email_sender.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('def process_followups():')
text = text[:idx]

follow_ups = '''def process_followups():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, email_sent_timestamp, last_followup_timestamp, followup_count FROM leads WHERE status = 'Sent' AND followup_count < 2 AND email_sent_timestamp IS NOT NULL")
        
        leads = cursor.fetchall()
        for lead in leads:
            now = datetime.utcnow()
            last_action_str = lead['last_followup_timestamp'] or lead['email_sent_timestamp']
            try:
                last_action = datetime.strptime(last_action_str, '%Y-%m-%d %H:%M:%S')
                diff_hours = (now - last_action).total_seconds() / 3600
                if diff_hours >= 48:
                    print(f"Triggering follow-up for {lead['email']}")
                    subject = "Checking in"
                    body = "We wanted to follow up on our previous email.\\n\\nThanks!"
                    to_email = lead['email']
                    
                    service = get_gmail_service()
                    msg = create_message(to_email, subject, body)
                    
                    sent_msg = service.users().messages().send(userId='me', body=msg).execute()
                    
                    cursor.execute("UPDATE leads SET followup_count = followup_count + 1, last_followup_timestamp = CURRENT_TIMESTAMP WHERE id = ?", (lead['id'],))
                    cursor.execute("INSERT INTO email_logs (lead_id, subject, body, sent_at, message_id) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)", (lead['id'], subject, body, sent_msg['id']))
                    conn.commit()
            except Exception as e:
                print(f"Error processing follow-up for lead {lead['id']}: {e}")
'''
text += follow_ups

with open(r'd:\Email\src\services\email_sender.py', 'w', encoding='utf-8') as f:
    f.write(text)
