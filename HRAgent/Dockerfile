FROM python:3.11-slim AS base

# curl is needed for container healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies in a separate layer for better cache reuse
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Initialise the SQLite database with seed data at image build time
RUN python hr_database.py

# Default command — overridden per-service in docker-compose.yml
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]
