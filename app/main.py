import os
import time
import logging
from fastapi import FastAPI, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.database import init_db, SessionLocal
from app.routes import router

# Configure Structured Logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", "message": "%(message)s"}'
)
logger = logging.getLogger("fitbuddy")

# Initialize Database
init_db()

# Rate Limiter setup (e.g. 60 requests/minute per IP)
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="FitBuddy – AI Fitness Plan Generator",
    description="Production-grade AI fitness planner powered by FastAPI, SQLAlchemy ORM, and Google Gemini models",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

templates = Jinja2Templates(directory="templates")

# Mount static folder
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")


# Structured Request/Response Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)

    logger.info(
        f'{{"client_ip": "{client_ip}", "method": "{request.method}", "path": "{request.url.path}", "status_code": {response.status_code}, "latency_ms": {duration_ms}}}'
    )
    return response


# Global Exception Handler with Graceful HTML Fallback
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f'{{"error": "{str(exc)}", "path": "{request.url.path}"}}')
    if "text/html" in request.headers.get("accept", ""):
        return HTMLResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>FitBuddy – Error</title>
                <style>
                    body {{ background: #0f172a; color: #f8fafc; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }}
                    .card {{ background: #1e293b; border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 32px; max-width: 500px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
                    h2 {{ color: #f87171; margin-bottom: 12px; }}
                    p {{ color: #94a3b8; font-size: 0.95rem; line-height: 1.5; margin-bottom: 20px; }}
                    a {{ display: inline-block; background: #6366f1; color: #fff; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 600; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h2>⚠️ Unable to Process Request</h2>
                    <p>An unexpected error occurred while processing your workout plan. Please ensure your Gemini API key is configured correctly and try again.</p>
                    <a href="/">← Return to Home</a>
                </div>
            </body>
            </html>
            """
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"status": "error", "message": "Internal server error. Please try again later."}
    )


# Healthcheck Endpoint
@app.get("/healthz", tags=["System"])
def health_check():
    api_key_configured = bool(os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_API_KEY") != "your_gemini_api_key_here")
    
    # Check Database connection
    db_healthy = True
    try:
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        db_healthy = False

    return {
        "status": "healthy" if (api_key_configured and db_healthy) else "degraded",
        "database": "connected" if db_healthy else "error",
        "gemini_api_configured": api_key_configured,
        "version": "1.0.0"
    }


# Include Application Routes
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
