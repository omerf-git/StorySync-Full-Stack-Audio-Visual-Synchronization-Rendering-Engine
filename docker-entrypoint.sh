#!/bin/bash
set -e

echo "============================================"
echo "  Google Images to Video - Starting..."
echo "============================================"

# Copy .env file to backend working directory (if exists)
if [ -f /app/backend/.env ]; then
    echo "[✓] .env file found."
else
    echo "[!] WARNING: /app/backend/.env file not found!"
    echo "    Provide the .env file from the environment section in Docker Compose or"
    echo "    via volume mount."
fi

# NVIDIA GPU check
if command -v nvidia-smi &> /dev/null; then
    echo "[✓] NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "    GPU info could not be read"
else
    echo "[!] WARNING: NVIDIA GPU not found. Whisper will run in CPU mode (might be slow)."
fi

# Start Nginx in the background
echo "[→] Starting Nginx (port 80)..."
nginx

# Start Uvicorn in the foreground
echo "[→] Starting Uvicorn (port 8005)..."
cd /app/backend
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8005 \
    --workers 1 \
    --timeout-keep-alive 300
