# ==============================================================================
# Multi-Stage Production Dockerfile for FitBuddy AI Fitness Plan Generator
# ==============================================================================

# Build Stage
FROM python:3.11-slim as builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final Stage
FROM python:3.11-slim as runner

WORKDIR /app

# Create non-root user for security
RUN groupadd -r fitbuddy && useradd -r -g fitbuddy -d /app fitbuddy

# Copy installed Python packages from builder stage
COPY --from=builder /root/.local /home/fitbuddy/.local
ENV PATH=/home/fitbuddy/.local/bin:$PATH

# Copy application source code and assets
COPY app/ /app/app/
COPY templates/ /app/templates/
COPY static/ /app/static/
COPY tests/ /app/tests/
COPY requirements.txt /app/

# Create data directory for persistent SQLite database & fix permissions
RUN mkdir -p /app/data && chown -R fitbuddy:fitbuddy /app

# Switch to non-root user
USER fitbuddy

# Expose FastAPI default port
EXPOSE 8000

# Environment defaults
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz')" || exit 1

# Production ASGI Entrypoint with Gunicorn + Uvicorn Workers
CMD ["gunicorn", "app.main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
