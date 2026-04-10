from apscheduler.schedulers.background import BackgroundScheduler
import time
from src.services.email_sender import process_email_queue, process_followups
from src.services.inbox_reader import process_inbox
import atexit

scheduler = BackgroundScheduler()


def _shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)

def start_scheduler():
    if scheduler.running:
        print("Scheduler already running; skipping duplicate startup.")
        return

    # Job to process inbox every 5 minutes
    scheduler.add_job(
        func=process_inbox,
        trigger="interval",
        minutes=5,
        id='inbox_job',
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Job to process email sending queue every 1 minute
    scheduler.add_job(
        func=process_email_queue,
        trigger="interval",
        minutes=1,
        id='email_queue_job',
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    # Job to process follow-ups every 1 hour
    scheduler.add_job(
        func=process_followups,
        trigger="interval",
        hours=1,
        id='followups_job',
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )

    scheduler.start()
    print("Scheduler started. Background tasks are running.")
    
    # Shut down the scheduler when exiting the app
    atexit.register(_shutdown_scheduler)

if __name__ == "__main__":
    start_scheduler()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
