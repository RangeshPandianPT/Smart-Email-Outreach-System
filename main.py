import os
import pandas as pd
import io
import tempfile
from fastapi import FastAPI, Request, Form, BackgroundTasks, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm
from contextlib import asynccontextmanager

from src.core.database import init_db, get_db
from src.core.models import Lead, EmailLog, Campaign, User
from src.services.lead_reader import import_leads_from_csv
from src.services.email_generator import generate_cold_email, generate_subject_line
from src.services.scheduler import start_scheduler
from src.services.inbox_reader import process_inbox
from src.core.validation import validate_gmail_credentials
from src.core.auth import get_current_user, create_access_token, verify_password, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
from src.tasks.celery_tasks import generate_all_pending_task, process_email_queue_task
from sqlalchemy.orm import Session
from datetime import timedelta
import uvicorn
from src.core.logger import setup_logger
from src.services.analytics import get_analytics_data, generate_insights

logger = setup_logger("main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    if not validate_gmail_credentials():
        logger.critical("Gmail credential validation failed. Application might not work as expected.")
    start_scheduler()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.post("/api/auth/signup")
async def signup(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == form_data.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(form_data.password)
    new_user = User(email=form_data.username, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}

@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/")
async def read_root():
    return {"status": "ok", "message": "Smart Email Outreach System API is running."}

@app.get("/api/leads")
async def get_all_leads(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    leads = db.query(Lead).order_by(Lead.id.desc()).all()
    return leads

@app.post("/api/import")
async def import_leads(file_path: str = Form("data/sample_leads.csv"), current_user: User = Depends(get_current_user)):
    resolved_path = file_path.strip()
    if not os.path.isabs(resolved_path) and not os.path.exists(resolved_path):
        fallback_path = os.path.join("data", resolved_path)
        if os.path.exists(fallback_path):
            resolved_path = fallback_path

    import_leads_from_csv(resolved_path)
    return {"status": "success", "message": "Leads imported successfully"}

@app.post("/api/generate/{lead_id}")
async def generate_email(lead_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    draft_created = False
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if lead and lead.status == 'Pending':
        lead_dict = {
            "id": lead.id, "name": lead.name, "role": lead.role, 
            "company": lead.company, "email": lead.email, 
            "service_needed": lead.service_needed,
            "status": lead.status, "deal_stage": lead.deal_stage
        }
        subject = generate_subject_line(lead_dict)
        body = generate_cold_email(lead_dict)
        
        if body and subject:
            email_log = EmailLog(lead_id=lead_id, subject=subject, body=body)
            db.add(email_log)
            lead.status = 'Drafted'
            db.commit()
            draft_created = True

    return {"status": "success", "draft_created": draft_created}

@app.post("/api/generate_all")
async def generate_all_pending(current_user: User = Depends(get_current_user)):
    generate_all_pending_task.delay()
    return {"status": "success", "message": "Background generation started via Celery"}

@app.post("/api/send_now")
async def send_now(current_user: User = Depends(get_current_user)):
    process_email_queue_task.delay()
    return {"status": "success", "message": "Email queue processing started via Celery"}

@app.get("/api/draft/{lead_id}")
async def get_draft(lead_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    draft = db.query(EmailLog).filter(EmailLog.lead_id == lead_id).order_by(EmailLog.id.desc()).first()
    if not draft:
        return JSONResponse(status_code=404, content={"message": "No draft found."})
    return draft

@app.post("/api/draft/{lead_id}")
async def save_draft(lead_id: int, subject: str = Form(...), body: str = Form(...), action: str = Form(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    draft = db.query(EmailLog).filter(EmailLog.lead_id == lead_id).order_by(EmailLog.id.desc()).first()
    if draft:
        draft.subject = subject
        draft.body = body
        lead = db.query(Lead).filter(Lead.id == lead_id).first()
        if lead:
            if action == 'approve':
                lead.status = 'Approved'
            else:
                lead.status = 'Drafted'
        db.commit()
    return {"status": "success", "message": f"Draft saved and set to {action}"}

@app.post("/api/approve_draft/{lead_id}")
async def approve_draft(lead_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if lead:
        lead.status = 'Approved'
        db.commit()
    return {"status": "success", "message": "Draft approved"}

@app.get("/fetch-replies-now")
async def fetch_replies_now(current_user: User = Depends(get_current_user)):
    try:
        logger.info("Manual reply fetch triggered")
        count = process_inbox()
        return {"status": "success", "message": "Replies fetched and updated", "count": count}
    except Exception as e:
        logger.error(f"Error in manual fetch: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/replies")
async def get_replies(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    replies = db.query(Lead.name, Lead.email, Lead.reply_status.label('status'), Lead.reply_text.label('reply')).filter(Lead.status == 'Replied').all()
    return [{"name": r.name, "email": r.email, "status": r.status, "reply": r.reply} for r in replies]

@app.post("/api/upload_csv")
async def upload_csv(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    if not file.filename.endswith(".csv"):
        return JSONResponse(status_code=400, content={"message": "Invalid file type. Please upload a .csv file."})

    try:
        content = await file.read()
        if not content:
            return JSONResponse(status_code=400, content={"message": "File is empty."})
            
        df_new = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        required_columns = ['Name', 'Email', 'Company', 'Role']
        missing_columns = [col for col in required_columns if col not in df_new.columns]
        
        if missing_columns:
            logger.warning("Invalid CSV format: Missing columns")
            return JSONResponse(status_code=400, content={"message": f"Invalid CSV format. Missing required columns: {', '.join(missing_columns)}"})

        if 'Status' not in df_new.columns:
            df_new['Status'] = "Not Sent"
        
        os.makedirs("data", exist_ok=True)
        csv_path = os.path.join("data", "leads.csv")
        
        if os.path.exists(csv_path):
            df_existing = pd.read_csv(csv_path)
            df_final = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_final = df_new
            
        df_final.to_csv(csv_path, index=False)
        logger.info("CSV uploaded successfully")
        logger.info("Leads appended to dataset")

        imported_count = 0
        temp_csv_path = None
        try:
            fd, temp_csv_path = tempfile.mkstemp(suffix=".csv")
            os.close(fd)
            df_new.to_csv(temp_csv_path, index=False)
            imported_count = import_leads_from_csv(temp_csv_path)
        except Exception as sync_err:
            logger.warning(f"CSV saved but DB sync failed: {sync_err}")
        finally:
            if temp_csv_path and os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)
        
        return {
            "status": "success",
            "message": f"Successfully uploaded {len(df_new)} leads to CSV. Imported {imported_count} new leads into dashboard."
        }
        
    except Exception as e:
        logger.error(f"Error handling CSV upload: {e}")
        return JSONResponse(status_code=500, content={"message": "An error occurred matching the CSV format."})


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "smart-email-outreach"}

@app.get("/api/dashboard")
async def get_dashboard_data(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        leads = db.query(Lead).order_by(Lead.id.desc()).all()

        analytics = get_analytics_data()
        analytics["insights"] = generate_insights(analytics)

        summary = {
            "total_leads": len(leads),
            "pending_leads": sum(1 for lead in leads if lead.status == "Pending"),
            "drafted_leads": sum(1 for lead in leads if lead.status == "Drafted"),
            "sent_leads": sum(1 for lead in leads if lead.status == "Sent"),
            "replied_leads": sum(1 for lead in leads if lead.status == "Replied"),
        }

        return {"leads": leads, "summary": summary, "analytics": analytics}
    except Exception as exc:
        logger.error(f"Error fetching dashboard data: {exc}")
        return {"leads": [], "summary": {}, "analytics": {}, "error": str(exc)}

@app.get("/api/analytics")
async def get_analytics(current_user: User = Depends(get_current_user)):
    try:
        data = get_analytics_data()
        data['insights'] = generate_insights(data)
        logger.info("Analytics updated")
        return data
    except Exception as e:
        logger.error(f"Error fetching analytics data: {e}")
        return {"error": str(e)}

@app.get("/api/campaigns")
async def view_campaigns(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        campaigns = db.query(Campaign).order_by(Campaign.id.desc()).all()
        return campaigns
    except Exception as e:
        logger.error(f"Failed to fetch campaigns: {e}")
        return []

@app.post("/api/campaigns/create")
async def create_campaign(name: str = Form(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        new_campaign = Campaign(name=name)
        db.add(new_campaign)
        db.commit()
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        return JSONResponse(status_code=500, content={"message": str(e)})
    return {"status": "success", "message": "Campaign created"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
