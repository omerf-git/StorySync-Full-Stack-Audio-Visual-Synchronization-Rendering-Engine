# ============================================================
# NVIDIA CUDA + Python Backend Dockerfile
# ============================================================
# Whisper için CUDA desteği ile tam donanımlı Python backend.
# FFmpeg (system), OpenCV (headless), Whisper (CUDA) dahil.
# ============================================================

# ── Stage 1: Frontend Build ──────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Önce sadece package dosyalarını kopyala (Docker cache optimizasyonu)
COPY frontend/package.json frontend/package-lock.json ./

RUN npm ci --production=false

# Kaynak kodu kopyala ve production build oluştur
COPY frontend/ ./

RUN npm run build


# ── Stage 2: Backend (CUDA destekli) ─────────────────────────
FROM nvidia/cuda:12.6.3-runtime-ubuntu24.04

# Ortam değişkenleri
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Whisper model cache'ini container içinde tut
    XDG_CACHE_HOME=/app/.cache

# Sistem bağımlılıkları
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    nginx \
    curl \
    # OpenCV headless için gerekli
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python sanal ortamı oluştur (system paketleriyle karışmayı önler)
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Önce sadece requirements.txt kopyala (Docker cache optimizasyonu)
COPY backend/requirements.txt ./requirements.txt

# PyTorch'u CUDA destekli olarak kur (Whisper bağımlılığı)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126 && \
    pip install --no-cache-dir -r requirements.txt

# Whisper modelini önceden indir (container başlatmada beklemeyi önler)
# "small" modeli varsayılan olarak kullanılıyor
RUN python3 -c "import whisper; whisper.load_model('small')"

# Backend kaynak kodunu kopyala
COPY backend/ ./backend/

# Frontend build çıktısını Nginx'in sunacağı yere kopyala
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Nginx konfigürasyonunu kopyala
COPY nginx.conf /etc/nginx/nginx.conf

# Başlatma scriptini kopyala
COPY docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh

# Portlar: 80 (Nginx → Frontend + API proxy)
EXPOSE 80

# Sağlık kontrolü
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:80/api/session/healthcheck 2>/dev/null || curl -f http://localhost:80/ || exit 1

ENTRYPOINT ["/app/docker-entrypoint.sh"]
