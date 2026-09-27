# ⚡ FitBuddy – AI Fitness Plan Generator

Production-grade full-stack web application and AI assistant built with **FastAPI**, **SQLAlchemy ORM**, **Jinja2 dynamic templating**, and **Google Gemini Models (`gemini-1.5-flash`)**.

---

## 🏗️ Architecture Diagram

```
+---------------------------------------------------------------------------------+
|                                 CLIENT BROWSER                                  |
|   - Intake Form (index.html)  - Plan View (result.html) - Admin (all_users.html)|
+----------------------------------------+----------------------------------------+
                                         | HTTP / JSON Requests
                                         v
+---------------------------------------------------------------------------------+
|                              FASTAPI APPLICATION                                |
|  - Structured Logging Middleware       - Rate Limiting (slowapi 60 req/min)     |
|  - Global Exception Boundaries         - Healthcheck (/healthz)                 |
|                                                                                 |
|  +--------------------+  +----------------------+  +--------------------------+ |
|  | Web Route Handlers |  | REST API Endpoints   |  | Jinja2 Template Engine   | |
|  +--------------------+  +----------------------+  +--------------------------+ |
+-------------------+-------------------+-------------------+---------------------+
                    |                   |                   |
                    v                   v                   v
     +-------------------------+        |        +-------------------------+
     |   SQLAlchemy ORM Layer  |        |        |   Google Gemini Engine  |
     | - User Model            |        |        | - gemini_generator      |
     | - WorkoutPlan Model     |        |        | - gemini_flash_generator|
     | - SQLite (fitbuddy.db)  |        |        | - updated_plan          |
     +-------------------------+        |        +-------------------------+
```

---

## 🚀 Quick Start & Local Setup

### 1. Prerequisites
- Python 3.10+
- Valid [Google Gemini API Key](https://aistudio.google.com/)

### 2. Manual Virtual Environment Setup
```powershell
# 1. Clone or navigate to the repository
cd "TN SKILL PRO"

# 2. Create isolated virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment variables in .env
echo "GOOGLE_API_KEY=your_actual_gemini_api_key_here" > .env

# 6. Initialize database
python -c "from app.database import init_db; init_db(); print('Database initialized!')"

# 7. Start development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

---

## 🧪 Automated Testing Suite

The test suite in `tests/test_fitbuddy.py` uses `pytest` and mocks Gemini API calls to execute instantaneously without consuming API tokens.

Run the test suite:
```bash
pytest -v tests/
```

**Coverage Includes**:
- ✅ Intake form rendering and POST handlers (`/generate-workout`)
- ✅ Feedback revision pipeline preserving original plan integrity (`/submit-feedback`)
- ✅ Admin user dashboard rendering (`/view-all-users`)
- ✅ Pydantic schema validation (preventing negative age, weight, or invalid fields)
- ✅ Database CRUD isolation using in-memory SQLite instances
- ✅ System health status endpoint (`/healthz`)

---

## 🐳 Docker Containerization

Run the containerized application using Docker and Docker Compose:

### Using Docker Compose (Recommended)
```bash
# Set your API key
export GOOGLE_API_KEY=your_gemini_key_here # Or place it in .env

# Build and start container in background
docker compose up --build -d

# View container logs
docker compose logs -f

# Check health status
docker compose ps
```

### Direct Docker Commands
```bash
# Build production multi-stage image
docker build -t fitbuddy:latest .

# Run container with volume mount for SQLite persistence
docker run -d \
  --name fitbuddy-app \
  -p 8000:8000 \
  -e GOOGLE_API_KEY="your_api_key_here" \
  -v fitbuddy_db_data:/app \
  fitbuddy:latest
```

---

## ☁️ Cloud Deployment Runbooks

### Option A: Render / Railway Deployment
1. Connect your GitHub repository to [Render](https://render.com) or [Railway](https://railway.app).
2. Set Environment Variable:
   - `GOOGLE_API_KEY` = `your_gemini_api_key`
3. Configure Start Command:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
   ```
4. Configure Healthcheck Path: `/healthz`.

### Option B: Cloud Run / VPS (Docker)
1. Push your built image to Google Artifact Registry / Docker Hub.
2. Deploy the container ensuring port `8000` or `$PORT` is mapped.
3. Attach persistent volume or Cloud SQL for database storage.

---

## 📖 REST API Reference

| Method | Endpoint | Description | Sample Payload / Params |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Web intake form interface | N/A |
| `POST` | `/generate-workout` | Web form submission | `name`, `user_id`, `age`, `weight`, `fitness_goal`, `intensity` |
| `POST` | `/submit-feedback` | Plan revision form | `user_id`, `feedback` |
| `GET` | `/view-all-users` | Web admin user records dashboard | N/A |
| `GET` | `/healthz` | System health & DB check | N/A |
| `POST` | `/api/generate-workout`| REST JSON endpoint for plan generation | `{"name":"Alex","user_id":"a1","age":28,"weight":75.0,"fitness_goal":"Fat Loss","intensity":"Beginner"}` |
| `POST` | `/api/submit-feedback` | REST JSON endpoint for plan revision | `{"user_id":"a1","feedback":"Swap squats with leg press"}` |
| `GET` | `/api/users` | REST JSON list of all users | N/A |
| `GET` | `/docs` | Interactive Swagger UI docs | N/A |

---

## 🔒 Security & Performance Features

- **Non-Root Execution**: Docker container runs as unprivileged user `fitbuddy`.
- **Rate Limiting**: Built-in `slowapi` rate limiter limits IP abuse (60 req/min).
- **Graceful Error Boundaries**: Beautiful HTML fallback cards protect users from raw stack traces.
- **Connection Isolation**: In-memory test sessions keep development and production databases clean.
- **Structured JSON Logging**: Standardized logs for ingestion into Datadog, CloudWatch, or Grafana.
