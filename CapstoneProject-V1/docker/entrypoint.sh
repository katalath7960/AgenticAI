#!/bin/bash
# docker/entrypoint.sh — container startup script
set -e

echo "=== Feedback Intelligence System ==="

# Ensure writable directories exist in mounted volumes
mkdir -p /app/data/input /app/data/output /app/data/chroma
mkdir -p /app/docs/product/user_uploads

# Create empty config.json if not present (gets populated by Streamlit UI)
if [ ! -f /app/config.json ]; then
    echo '{}' > /app/config.json
    echo "[init] Created empty config.json"
fi

echo "[init] Data dir:      $DATA_DIR"
echo "[init] Output dir:    $OUTPUT_DIR"
echo "[init] ChromaDB path: $CHROMA_PATH"
echo "[init] Tech docs dir: $TECH_DOCS_DIR"
echo "[init] Starting Streamlit on http://0.0.0.0:8501 ..."

exec streamlit run ui/app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true
