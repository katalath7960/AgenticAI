# ── Feedback Intelligence System ─────────────────────────────────────────────
# Single-stage image: Streamlit UI + LangGraph pipeline
#
# Build:  docker build -t feedback-intelligence .
# Run:    docker-compose up
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# System build deps (gcc for chromadb/pydantic; curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        curl \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Python dependencies ───────────────────────────────────────────────────────
# Copy requirements first so Docker layer cache is reused on code-only changes
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# ── Application source ────────────────────────────────────────────────────────
COPY src/       ./src/
COPY ui/        ./ui/
COPY docs/      ./docs/
COPY scripts/   ./scripts/

# Create writable data directories and default config (volumes override at runtime)
RUN mkdir -p data/input data/output data/chroma docs/product/user_uploads \
 && echo '{}' > config.json

# ── Streamlit server config (headless, no XSRF so health check works) ─────────
RUN mkdir -p /root/.streamlit && \
    printf '[server]\nheadless = true\nenableCORS = false\nenableXsrfProtection = false\nport = 8501\naddress = "0.0.0.0"\n\n[browser]\ngatherUsageStats = false\n' \
    > /root/.streamlit/config.toml

# ── Port ──────────────────────────────────────────────────────────────────────
EXPOSE 8501

# ── Healthcheck ───────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# ── Startup — inline shell avoids Windows CRLF issues with script files ───────
CMD ["sh", "-c", \
     "mkdir -p /app/data/input /app/data/output /app/data/chroma /app/docs/product/user_uploads && \
      [ -f /app/config.json ] || echo '{}' > /app/config.json && \
      exec streamlit run ui/app.py --server.port=8501 --server.address=0.0.0.0"]
