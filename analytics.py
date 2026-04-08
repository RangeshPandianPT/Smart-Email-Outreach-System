import sqlite3
from database import get_db_connection

def get_analytics_data():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Total sent
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status IN ('Sent', 'Replied')")
        total_sent = cursor.fetchone()[0]
        
        # Total replies
        cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'Replied'")
        total_replies = cursor.fetchone()[0]
        
        # Breakdown by status
        cursor.execute("SELECT reply_status, COUNT(*) FROM leads WHERE status = 'Replied' GROUP BY reply_status")
        breakdown = {row[0]: row[1] for row in cursor.fetchall()}
        
        interested = breakdown.get('Interested', 0)
        not_interested = breakdown.get('Not Interested', 0)
        meeting_requests = breakdown.get('Meeting Request', 0)
        
        # Conversion rate
        conversion_rate = 0.0
        if total_sent > 0:
            conversion_rate = round((interested / total_sent) * 100, 2)
            
        # Average response time
        # Convert timestamp strings to julianday difference, multiply by 24 for hours
        cursor.execute("""
            SELECT AVG(
                (julianday(reply_timestamp) - julianday(email_sent_timestamp)) * 24
            )
            FROM leads 
            WHERE reply_timestamp IS NOT NULL 
              AND email_sent_timestamp IS NOT NULL
              AND status = 'Replied'
        """)
        avg_rt = cursor.fetchone()[0]
        avg_response_time_hours = round(avg_rt, 2) if avg_rt else 0.0
        
        return {
            "total_sent": total_sent,
            "total_replies": total_replies,
            "interested": interested,
            "not_interested": not_interested,
            "meeting_requests": meeting_requests,
            "conversion_rate": conversion_rate,
            "avg_response_time_hours": avg_response_time_hours
        }

def generate_insights(analytics_data):
    insights = []
    
    total_sent = analytics_data["total_sent"]
    replies = analytics_data["total_replies"]
    interested = analytics_data["interested"]
    avg_hours = analytics_data["avg_response_time_hours"]
    
    if total_sent == 0:
        insights.append("No emails sent yet to analyze.")
        return insights
        
    reply_rate = (replies / total_sent) * 100
    if reply_rate > 20:
        insights.append(f"Excellent reply rate of {reply_rate:.1f}%.")
    elif reply_rate > 0:
        insights.append(f"Current reply rate is {reply_rate:.1f}%.")
    else:
        insights.append("Awaiting your first reply.")
        
    if avg_hours > 0:
        if avg_hours < 24:
            insights.append(f"Fast average response time of {avg_hours} hours. Most replies come within 24 hours.")
        else:
            insights.append(f"Average response time is {avg_hours} hours.")
            
    if replies > 0:
        interested_percent = (interested / replies) * 100
        if interested_percent > 30:
            insights.append(f"High quality leads: {interested_percent:.1f}% of replies are Interested.")
            
    return insights
