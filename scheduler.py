from apscheduler.schedulers.background import BackgroundScheduler
import time
from email_sender import process_email_queue
from inbox_reader import process_inbox
import atexit

scheduler = BackgroundScheduler()

def start_scheduler():
    # Job to process inbox every 5 minutes
    scheduler.add_job(func=process_inbox, trigger="interval", minutes=5, id='inbox_job')
    
    # Job to process email sending queue every 1 minute
    scheduler.add_job(func=process_email_queue, trigger="interval", minutes=1, id='email_queue_job')
    
    scheduler.start()
    print("Scheduler started. Background tasks are running.")
    
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    start_scheduler()
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break
