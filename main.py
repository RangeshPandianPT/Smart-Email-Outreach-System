import os
import pandas as pd
import io
import tempfile
from fastapi import FastAPI, Request, Form, BackgroundTasks, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from database import get_db_connection, init_db
from lead_reader import import_leads_from_csv
from email_generator import generate_cold_email, generate_subject_line
from scheduler import start_scheduler
from inbox_reader import process_inbox
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


@app.get("/fetch-replies-now")
async def fetch_replies_now():
    try:
        print("Manual reply fetch triggered")
        count = process_inbox()
        return {"status": "success", "message": "Replies fetched and updated", "count": count}
    except Exception as e:
        print(f"Error in manual fetch: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/api/replies")
async def get_replies():
    """
    Fetch all leads that have replied.
    Returns JSON format for the dashboard.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name, email, reply_status as status, reply_text as reply FROM leads WHERE status = 'Replied'")
            replies = [dict(row) for row in cursor.fetchall()]
            return replies
        except Exception as e:
            print("Error fetching replies from DB:", e)
            return []

@app.post("/upload_csv", response_class=HTMLResponse)
async def upload_csv(file: UploadFile = File(...)):
    """
    Handle CSV uploads, validate format, append to existing dataset,
    and save back for backend worker processes to pick up.
    """
    if not file.filename.endswith(".csv"):
        return "<p>Invalid file type. Please upload a .csv file.</p><br><a href='/'>Back</a>"

    try:
        content = await file.read()
        if not content:
            return "<p>File is empty.</p><br><a href='/'>Back</a>"
            
        # Parse with Pandas
        df_new = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        # 4. Data Validation: Required columns
        required_columns = ['Name', 'Email', 'Company', 'Role']
        missing_columns = [col for col in required_columns if col not in df_new.columns]
        
        if missing_columns:
            print("Invalid CSV format: Missing columns")
            return f"<p>Invalid CSV format. Missing required columns: {', '.join(missing_columns)}</p><br><a href='/'>Back</a>"

        # 5. Status Column Handling
        if 'Status' not in df_new.columns:
            df_new['Status'] = "Not Sent"
        
        # 9. Ensure data/ exists and leads.csv is ready
        os.makedirs("data", exist_ok=True)
        csv_path = os.path.join("data", "leads.csv")
        
        # 3. Append to existing CSV (Option B)
        if os.path.exists(csv_path):
            df_existing = pd.read_csv(csv_path)
            # Merge uploaded with existing data
            df_final = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df_final = df_new
            
        df_final.to_csv(csv_path, index=False)
        print("CSV uploaded successfully")
        print("Leads appended to dataset")

        # Sync uploaded rows into SQLite so they appear immediately on dashboard
        imported_count = 0
        temp_csv_path = None
        try:
            fd, temp_csv_path = tempfile.mkstemp(suffix=".csv")
            os.close(fd)
            df_new.to_csv(temp_csv_path, index=False)
            imported_count = import_leads_from_csv(temp_csv_path)
        except Exception as sync_err:
            print(f"Warning: CSV saved but DB sync failed: {sync_err}")
        finally:
            if temp_csv_path and os.path.exists(temp_csv_path):
                os.remove(temp_csv_path)
        
        # Provide success message and lead count
        return (
            f"<p>Successfully uploaded {len(df_new)} leads to CSV. "
            f"Imported {imported_count} new leads into dashboard.</p>"
            "<br><a href='/'>Back to Dashboard</a>"
        )
        
    except Exception as e:
        print(f"Error handling CSV upload: {e}")
        return f"<p>An error occurred matching the CSV format.</p><br><a href='/'>Back</a>"

from analytics import get_analytics_data, generate_insights

@app.get("/api/analytics")
async def get_analytics():
    try:
        data = get_analytics_data()
        data['insights'] = generate_insights(data)
        print("Analytics updated")
        return data
    except Exception as e:
        print(f"Error fetching analytics data: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
