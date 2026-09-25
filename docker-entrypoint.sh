#!/bin/bash
set -e

echo "============================================"
echo "  Google Images to Video - Starting..."
echo "============================================"

# .env dosyasını backend çalışma dizinine kopyala (eğer varsa)
if [ -f /app/backend/.env ]; then
    echo "[✓] .env dosyası bulundu."
else
    echo "[!] UYARI: /app/backend/.env dosyası bulunamadı!"
    echo "    Docker Compose'da environment bölümünden veya"
    echo "    volume mount ile .env dosyasını sağlayın."
fi

# NVIDIA GPU kontrolü
if command -v nvidia-smi &> /dev/null; then
    echo "[✓] NVIDIA GPU algılandı:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "    GPU bilgisi okunamadı"
else
    echo "[!] UYARI: NVIDIA GPU bulunamadı. Whisper CPU modunda çalışacak (yavaş olabilir)."
fi

# Nginx'i arka planda başlat
echo "[→] Nginx başlatılıyor (port 80)..."
nginx

# Uvicorn'u ön planda başlat
echo "[→] Uvicorn başlatılıyor (port 8005)..."
cd /app/backend
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8005 \
    --workers 1 \
    --timeout-keep-alive 300
