# Smart Email Outreach System - Comprehensive Implementation Plan

Given the scope of the request ("implement all now"), the work is broken down into structured, actionable phases. We are executing these phases concurrently where possible to ensure rapid delivery while maintaining system stability.

## Phase 1: Frontend Modernization (Currently In Progress)
- [x] Scaffold modern Vite + React + TypeScript application (`/frontend`).
- [x] Configure Tailwind CSS for modern aesthetics (glassmorphism, dark mode).
- [ ] Refactor FastAPI to serve purely as a JSON REST API (removing Jinja2 templates).
- [x] Implement responsive React components for Dashboard, Leads Table, and Analytics.
- [ ] Add micro-animations and data visualizations using `recharts` or `chart.js` in React.

## Phase 2: Architectural Upgrades (PostgreSQL & Redis)
- [x] Update `docker-compose.yml` to include PostgreSQL and Redis services.
- [ ] Migrate `database.py` and raw SQLite queries across the application to SQLAlchemy ORM to support Postgres seamlessly without syntax clashes.
- [ ] Implement Celery for robust background task scheduling, replacing FastAPI's `BackgroundTasks` for reliability in email processing.
- [x] Update `requirements.txt` with `psycopg2`, `redis`, `celery`, and `sqlalchemy`.

## Phase 3: Multi-User Authentication & Security
- [ ] Add `users` table to the database.
- [ ] Implement JWT-based authentication in FastAPI.
- [ ] Add Login/Signup UI in the React frontend.
- [ ] Secure all API endpoints using FastAPI dependency injection (`Depends(get_current_user)`).
- [ ] Scope leads and email templates by `user_id`.

## Phase 4: Advanced AI Context & Dynamic Follow-ups
- [ ] Implement a basic Vector Store (e.g., ChromaDB) or simple RAG mechanism allowing users to upload text files (case studies).
- [ ] Modify `email_generator.py` to fetch relevant context from the RAG store before generating emails to enhance personalization.
- [ ] Develop an automated Celery beat task to scan the database daily and queue `generate_followup_email` for leads in the 'Sent' stage longer than 3 days.

## Phase 5: Testing & CI/CD
- [ ] Expand pytest coverage for new async endpoints and database models.
- [ ] Create `.github/workflows/deploy.yml` for automated testing and deployment.
- [ ] Finalize Dockerfiles for both Backend and Frontend.
