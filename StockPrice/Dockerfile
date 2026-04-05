FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY agent.py dashboard.py ./

# watchlist persisted via a mounted volume
VOLUME ["/app/data"]
ENV WATCHLIST_FILE=/app/data/watchlist.json

EXPOSE 8501
