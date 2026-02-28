# ── Stage 1: base image ───────────────────────────────────────────────────────
FROM python:3.11-slim AS base

# System dependencies (curl used for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies in a separate layer for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# ── Default command (overridden per-service in docker-compose) ─────────────────
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
