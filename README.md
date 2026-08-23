# CampusOS AI — Smart Campus Assistant

This repository contains the CampusOS AI-powered student assistant and administrative coordinator codebase.

## Standardized Development Environment

The project is standardized to run on a single Python environment (supporting Python 3.10+).

### Backend Setup

1. **Activate Environment / Navigate**:
   ```bash
   cd backend
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Database Seeding**:
   To initialize and seed the SQLite database with mock data (admin and student accounts):
   ```bash
   python backend/scripts/seed_db.py
   ```
4. **Data Migration**:
   To migrate any legacy JSON data stores into the SQLite database:
   ```bash
   python backend/scripts/migrate_json_to_sqlite.py
   ```
5. **Start Uvicorn Server**:
   ```bash
   python -m uvicorn backend.main:app --port 8000 --reload
   ```

### Frontend Setup

1. **Navigate**:
   ```bash
   cd frontend
   ```
2. **Install Packages**:
   ```bash
   npm install
   ```
3. **Start Development Server**:
   ```bash
   npm run dev
   ```

## Architecture

* **Frontend**: React SPA (Vite) with Axios client communicating with the backend.
* **Backend**: FastAPI web server.
* **Orchestration**: LangGraph workflow for AI multi-agent cooperation.
* **Storage**: Single source of truth SQLite database (`campus.db`) for all mutable state data.
