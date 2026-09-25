<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/NVIDIA_CUDA-76B900?style=for-the-badge&logo=nvidia&logoColor=white" alt="CUDA">
  <img src="https://img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white" alt="FFmpeg">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">
</p>

# 🎬 Google Images to Video

**Metin tabanlı belgesel/hikaye anlatımını, yapay zeka destekli görsel arama ve ses senkronizasyonu ile profesyonel video segmentlerine dönüştüren tam yığın (full-stack) uygulama.**

Bir ses kaydı ve metin girişi alır; metni AI ile parçalara ayırır, Whisper ile ses-metin eşleştirmesi yapar, Google Images'tan otomatik görsel arar ve her parça için **birebir ses senkronizasyonlu MP4 video segmentleri** üretir.

---

## 📋 İçindekiler

- [Özellikler](#-özellikler)
- [Mimari](#-mimari)
- [Demo Akışı](#-demo-akışı)
- [Hızlı Başlangıç (Docker)](#-hızlı-başlangıç-docker)
- [Manuel Kurulum (Geliştirme)](#-manuel-kurulum-geliştirme)
- [API Anahtarları](#-api-anahtarları)
- [Proje Yapısı](#-proje-yapısı)
- [API Referansı](#-api-referansı)
- [Teknik Detaylar](#-teknik-detaylar)
- [Sorun Giderme](#-sorun-giderme)
- [Lisans](#-lisans)

---

## ✨ Özellikler

| Özellik | Açıklama |
|---------|----------|
| 🤖 **AI Metin Segmentasyonu** | Gemini API ile belgesel metnini anlamlı parçalara ayırır |
| 🎙️ **Whisper Ses Analizi** | OpenAI Whisper ile kelime bazında zaman damgası çıkarır (GPU hızlandırmalı) |
| 🔍 **Otomatik Görsel Arama** | Google Images üzerinden her parça için bağlamsal görsel arar |
| 🎬 **Video Üretimi** | FFmpeg ile birebir ses senkronizasyonlu MP4 segmentleri oluşturur |
| 🎯 **Frame-Aligned Sync** | 30 FPS kare hizalama ile sıfır birikimli kayma (drift) garantisi |
| 📱 **Modern Web UI** | React + Vite ile responsive, dark-mode arayüz |
| 🐳 **Docker Ready** | Tek komutla NVIDIA GPU destekli deployment |
| 💾 **Session Yönetimi** | Sayfa yenilense bile kaldığınız yerden devam |

---

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Container                      │
│                                                         │
│  ┌──────────┐     ┌────────────────────────────────┐   │
│  │  Nginx   │────▶│  React Frontend (Static)       │   │
│  │  :80     │     │  - UploadView                  │   │
│  │          │     │  - ReviewView                   │   │
│  │          │     │  - StudioView                   │   │
│  │          │     └────────────────────────────────┘   │
│  │          │                                          │
│  │          │     ┌────────────────────────────────┐   │
│  │  /api/* ─┼────▶│  FastAPI Backend (Uvicorn)     │   │
│  └──────────┘     │  :8005                         │   │
│                   │                                 │   │
│                   │  ┌───────────┐ ┌─────────────┐ │   │
│                   │  │ Gemini AI │ │   Whisper    │ │   │
│                   │  │ (Metin)   │ │ (Ses→Metin)  │ │   │
│                   │  └───────────┘ └──────┬──────┘ │   │
│                   │                       │        │   │
│                   │  ┌───────────┐ ┌──────▼──────┐ │   │
│                   │  │  Serper   │ │  NVIDIA GPU │ │   │
│                   │  │ (Görseller)│ │   (CUDA)   │ │   │
│                   │  └───────────┘ └─────────────┘ │   │
│                   │                                 │   │
│                   │  ┌─────────────────────────┐   │   │
│                   │  │  FFmpeg (Video Üretimi)  │   │   │
│                   │  └─────────────────────────┘   │   │
│                   └────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 🎬 Demo Akışı

### 1️⃣ Proje Başlat
Ses dosyanızı (MP3/WAV) ve belgesel metninizi yükleyin. AI metni otomatik olarak parçalara ayırır ve Whisper ile ses-metin eşleştirmesi yapar.

### 2️⃣ Zaman Damgası İnceleme
AI'ın eşleştirmesini kontrol edin. Sorunlu eşleşmeleri düzenleyip onaylayın.

### 3️⃣ Stüdyo
Her parça için Google Images'tan gelen görseller arasından birini seçin. Seçtiğiniz anda video oluşturulur ve otomatik indirilir.

### 4️⃣ Birleştirme
İndirilen MP4 segmentlerini sırasıyla CapCut, DaVinci Resolve veya herhangi bir video düzenleyicide birleştirin. Ses senkronizasyonu kusursuzdur.

---

## 🐳 Hızlı Başlangıç (Docker)

### Gereksinimler

| Bileşen | Minimum | Önerilen |
|---------|---------|----------|
| **Docker Engine** | 24.0+ | Son sürüm |
| **RAM** | 4 GB | 8 GB+ |
| **Disk** | 10 GB | 20 GB+ |
| **GPU** | - | NVIDIA (CUDA 12.x) |

### NVIDIA GPU ile (Önerilen)

```bash
# 1. NVIDIA Container Toolkit kurulumu (sadece ilk seferde)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 2. Projeyi klonla
git clone https://github.com/YOUR_USERNAME/google_images_to_video.git
cd google_images_to_video

# 3. API anahtarlarını ayarla
cp backend/.env.example backend/.env
nano backend/.env  # Kendi API key'lerinizi girin

# 4. Build ve çalıştır
docker compose up -d --build

# 5. Tarayıcıda aç
# http://localhost
```

### GPU Olmadan (CPU Only)

```bash
# Aynı adımları takip edin, sadece 4. adımda şu komutu kullanın:
docker compose -f docker-compose.cpu.yml up -d --build
```

> ⚠️ CPU modunda Whisper ~3-5x daha yavaş çalışır ancak tüm fonksiyonlar sorunsuz çalışır.

---

## 🛠️ Manuel Kurulum (Geliştirme)

### Gereksinimler

- Python 3.10+
- Node.js 18+
- FFmpeg
- (Opsiyonel) NVIDIA GPU + CUDA

### Backend

```bash
# Sanal ortam oluştur
python3 -m venv venv
source venv/bin/activate

# Bağımlılıkları kur
cd backend
pip install -r requirements.txt

# PyTorch CUDA (GPU varsa)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# API anahtarlarını ayarla
cp .env.example .env
nano .env

# Sunucuyu başlat
uvicorn app.main:app --host 0.0.0.0 --port 8005
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Tarayıcıda `http://localhost:3000` adresini açın.

---

## 🔑 API Anahtarları

Bu uygulama 2 harici API servisi kullanır:

| Servis | Amaç | Ücretsiz Plan | Nereden Alınır |
|--------|-------|---------------|----------------|
| **Gemini API** | Metin segmentasyonu ve çeviri | ✅ Günlük 1500 istek | [Google AI Studio](https://aistudio.google.com/apikey) |
| **Serper API** | Google Images görsel arama | ✅ Aylık 2500 arama | [serper.dev](https://serper.dev) |

API anahtarlarınızı `backend/.env` dosyasına yazın:

```env
GEMINI_API_KEY=your_gemini_api_key_here
SERPER_API_KEY=your_serper_api_key_here
```

---

## 📁 Proje Yapısı

```
google_images_to_video/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI uç noktaları & session yönetimi
│   │   └── services/
│   │       ├── text_to_json.py     # Gemini AI ile metin segmentasyonu
│   │       ├── audio_processing.py # Whisper ile ses-metin eşleştirmesi
│   │       ├── image_search.py     # Serper API ile Google Images arama
│   │       └── video_generation.py # FFmpeg ile video üretimi
│   ├── system_prompt.txt           # Gemini AI sistem talimatı
│   ├── requirements.txt            # Python bağımlılıkları
│   ├── .env.example                # Örnek ortam değişkenleri
│   └── .env                        # API anahtarları (git'e dahil edilmez)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Ana uygulama bileşeni
│   │   ├── components/
│   │   │   ├── UploadView.jsx      # Ses ve metin yükleme sayfası
│   │   │   ├── ReviewView.jsx      # Zaman damgası inceleme sayfası
│   │   │   └── StudioView.jsx      # Görsel seçimi ve video üretimi
│   │   ├── index.css               # Global stiller (dark theme)
│   │   └── main.jsx                # React entry point
│   ├── package.json
│   └── vite.config.js              # Vite + API proxy ayarları
│
├── Dockerfile                      # Multi-stage build (React + CUDA Python)
├── docker-compose.yml              # GPU destekli deployment
├── docker-compose.cpu.yml          # CPU-only deployment
├── nginx.conf                      # Reverse proxy konfigürasyonu
├── docker-entrypoint.sh            # Container başlatma scripti
├── .gitignore
├── .dockerignore
├── LICENSE
└── README.md
```

---

## 📡 API Referansı

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| `POST` | `/api/analyze` | Ses + metin yükle, AI analizi başlat |
| `GET` | `/api/session/{id}` | Session bilgilerini getir |
| `POST` | `/api/session/{id}/confirm` | Zaman damgalarını onayla |
| `GET` | `/api/session/{id}/images` | Mevcut parça için görselleri getir |
| `POST` | `/api/session/{id}/generate_video` | Seçilen görsel ile video oluştur |
| `POST` | `/api/session/{id}/next` | Sonraki parçaya geç |
| `POST` | `/api/session/{id}/prev` | Önceki parçaya dön |
| `POST` | `/api/session/{id}/next_keyword` | Farklı anahtar kelime ile ara |
| `GET` | `/api/session/healthcheck` | Sağlık kontrolü |

Detaylı API dokümantasyonu: `http://localhost:8005/docs` (Swagger UI)

---

## 🔧 Teknik Detaylar

### Ses-Video Senkronizasyonu

Bu uygulama, video segmentleri arasında **sıfır birikimli kayma (zero cumulative drift)** garantisi sağlar:

1. **Frame-Aligned Timestamps**: Tüm zaman damgaları `1/30 saniye` katlarına hizalanır
2. **WAV Extraction**: Ses önce PCM/WAV formatına çıkarılır (sample-accurate kesim)
3. **Matched Duration**: Video ve ses track'leri birebir aynı sürede üretilir
4. **Sequential Boundary Sync**: Ardışık segmentlerin sınır noktaları eşitlenir

### Whisper Modeli

Varsayılan olarak `small` modeli kullanılır. Daha yüksek doğruluk için `medium` veya `large-v3` kullanılabilir (`audio_processing.py` içinde `model_name` parametresi).

| Model | VRAM | Hız | Doğruluk |
|-------|------|-----|----------|
| tiny | ~1 GB | ⚡⚡⚡⚡ | ★★☆☆ |
| small | ~2 GB | ⚡⚡⚡ | ★★★☆ |
| medium | ~5 GB | ⚡⚡ | ★★★★ |
| large-v3 | ~10 GB | ⚡ | ★★★★★ |

### Filigran Filtreleme

Görsel arama sonuçlarından filigran içermesi muhtemel kaynaklar (Getty Images, Shutterstock, iStock vb.) otomatik olarak filtrelenir.

---

## 🐛 Sorun Giderme

<details>
<summary><strong>Docker build çok uzun sürüyor</strong></summary>

İlk build ~10-15 dakika sürebilir (PyTorch + CUDA indirmesi). Sonraki build'ler Docker cache sayesinde çok daha hızlıdır. `docker compose build --no-cache` ile tamamen sıfırdan build alabilirsiniz.
</details>

<details>
<summary><strong>GPU algılanmıyor</strong></summary>

```bash
# NVIDIA sürücüsünü kontrol et
nvidia-smi

# NVIDIA Container Toolkit kurulu mu?
dpkg -l | grep nvidia-container-toolkit

# Docker runtime doğru mu?
docker info | grep -i runtime
```
</details>

<details>
<summary><strong>"Bu görselin kaynak sitesi indirmeye izin vermiyor" hatası</strong></summary>

Bazı web siteleri bot erişimini engelliyor. Farklı bir görsel seçin veya 🔑 butonu ile farklı bir anahtar kelime deneyin.
</details>

<details>
<summary><strong>Whisper çok yavaş çalışıyor</strong></summary>

CPU modunda Whisper yavaştır. NVIDIA GPU'nuz varsa `docker-compose.yml` (GPU versiyonu) kullandığınızdan emin olun. GPU varsa ~5-10x hızlanma sağlanır.
</details>

<details>
<summary><strong>Sayfa yenileyince ana sayfaya dönüyor</strong></summary>

Backend sunucusu yeniden başlatılmışsa in-memory session'lar silinir. Sunucunun çalıştığından emin olun: `docker compose ps`
</details>

---

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.

---

<p align="center">
  <sub>Built with ❤️ using Python, React, Whisper, Gemini & FFmpeg</sub>
</p>
