import os
from fastapi import FastAPI, Request, Form, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from database import get_db_connection, init_db
from lead_reader import import_leads_from_csv
from email_generator import generate_cold_email, generate_subject_line
from scheduler import start_scheduler
import uvicorn

app = FastAPI(title="VFX Email Outreach System")

# Ensure template directory exists
os.makedirs("templates", exist_ok=True)
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def on_startup():
    init_db()
    start_scheduler()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads ORDER BY id DESC")
        leads_raw = cursor.fetchall()
        
        leads = [dict(lead) for lead in leads_raw]
        
    return templates.TemplateResponse("index.html", {"request": request, "leads": leads})

@app.post("/import")
async def import_leads(file_path: str = Form("sample_leads.csv")):
    import_leads_from_csv(file_path)
    return RedirectResponse(url="/", status_code=303)

@app.post("/generate/{lead_id}")
async def generate_email(lead_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        lead = cursor.fetchone()
        
        if lead and lead['status'] == 'Pending':
            subject = generate_subject_line(lead)
            body = generate_cold_email(lead)
            
            if body and subject:
                cursor.execute("""
                    INSERT INTO email_logs (lead_id, subject, body)
                    VALUES (?, ?, ?)
                """, (lead_id, subject, body))
                
                cursor.execute("UPDATE leads SET status = 'Drafted' WHERE id = ?", (lead_id,))
                
    return RedirectResponse(url="/", status_code=303)

@app.post("/generate_all")
async def generate_all_pending(background_tasks: BackgroundTasks):
    def _generate_all():
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM leads WHERE status = 'Pending'")
            pending = cursor.fetchall()
            
            for lead in pending:
                subject = generate_subject_line(lead)
                body = generate_cold_email(lead)
                
                if body and subject:
                    cursor.execute("""
                        INSERT INTO email_logs (lead_id, subject, body)
                        VALUES (?, ?, ?)
                    """, (lead['id'], subject, body))
                    cursor.execute("UPDATE leads SET status = 'Drafted' WHERE id = ?", (lead['id'],))
                    conn.commit() # commit each to show progress
                    
    background_tasks.add_task(_generate_all)
    return RedirectResponse(url="/", status_code=303)

@app.get("/view_draft/{lead_id}", response_class=HTMLResponse)
async def view_draft(request: Request, lead_id: int):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM email_logs WHERE lead_id = ? ORDER BY id DESC LIMIT 1", (lead_id,))
        draft = cursor.fetchone()
        
    if not draft:
        return "<p>No draft found.</p><a href='/'>Back</a>"
        
    return f"""
    <h2>Subject: {draft['subject']}</h2>
    <hr>
    <pre style='white-space: pre-wrap; font-family: sans-serif;'>{draft['body']}</pre>
    <br><a href='/'>Back to Dashboard</a>
    """

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
