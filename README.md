# Smart Email Outreach System

A professional-grade, automated email outreach and lead management system. This application integrates directly with Gmail to intelligently process leads, classify responses, generate personalized emails, schedule outreach campaigns, and provide analytical insights into your email outreach performance.

## 🚀 Features

- **Automated Email Generation:** Dynamically generate personalized emails for your leads.
- **Intelligent Classification:** Automatically classify incoming responses and analyze inbox sentiment.
- **Lead Processing:** Import, validate, and process lead information systematically.
- **Gmail Integration:** Securely connect and interact with your Gmail account.
- **Campaign Scheduling:** Schedule automated email follow-ups and outreach tasks.
- **Data Analytics:** Track engagement and outreach metrics.

## 📂 Project Structure

The project follows a clean, modular architecture:

```text
├── data/                       # Directory for localized data (e.g., sample_leads.csv)
├── src/                        # Source code for the application
│   ├── core/                   # Core application configurations and database management
│   │   ├── config.py           # Application configuration
│   │   ├── database.py         # Database connection and queries
│   │   ├── credentials.json    # OAuth 2.0 Credentials (ignored in version control)
│   │   └── token.json          # Authenticated session token (ignored in version control)
│   ├── services/               # Business logic and external service integrations
│   │   ├── analytics.py        # Campaign analytics and metrics
│   │   ├── classifier.py       # Inbox response classification
│   │   ├── email_generator.py  # Automated email content generation
│   │   ├── email_sender.py     # Email dispatching logic
│   │   ├── gmail_client.py     # Gmail API client wrapper
│   │   ├── inbox_reader.py     # Inbox polling and reading
│   │   ├── lead_processor.py   # Lead management and routing
│   │   ├── lead_reader.py      # Lead parsing (e.g., CSV/DB ingestion)
│   │   ├── notifier.py         # Notifications and alerts
│   │   └── scheduler.py        # Task scheduling and background jobs
│   └── scripts/                # Utility scripts for maintenance and fixes
│       ├── check.py            # System sanity checks
│       ├── fix.py              # Assorted system fixes
│       ├── fix2.py             # Assorted system fixes
│       ├── modify_database_done.py # Database migration/correction utility
│       └── script.py           # General execution script
├── templates/                  # HTML templates for notifications or frontend
│   └── index.html              
├── main.py                     # Application entry point
└── requirements.txt            # Python dependencies
```

## 🛠️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Smart-Email-Outreach-System
   ```

2. **Set up a virtual environment (Recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Authentication:**
   - Place your Google API `credentials.json` inside the `src/core/` directory.
   - In `.env`, set `GCP_CREDENTIALS_PATH=src/core/credentials.json`.
   - Upon first run, the system will generate a `token.json` file in `src/core/` to store your session.
   - Optional auth check: `python -m src.services.gmail_client`

### Deploying on Render (Important)

Render is a headless environment, so browser-based OAuth (`run_local_server`) cannot run there.

- Generate Gmail OAuth once on your local machine to obtain `token.json` (contains refresh token).
- In Render environment variables, set:
   - `APP_ENV=production`
   - `GMAIL_TOKEN_JSON` to the full JSON content of your local `token.json`
   - Optional: `GMAIL_CREDENTIALS_JSON` to full `credentials.json` content
- Alternative: mount secret files and set `GCP_CREDENTIALS_PATH` and `GMAIL_TOKEN_PATH` accordingly.

If no valid token is available in production, email sending will fail by design with a clear runtime error.

## 💻 Usage

To start the main application or scheduling daemon:

```bash
python main.py
```

