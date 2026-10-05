<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/NVIDIA_CUDA-76B900?style=for-the-badge&logo=nvidia&logoColor=white" alt="CUDA">
  <img src="https://img.shields.io/badge/FFmpeg-007808?style=for-the-badge&logo=ffmpeg&logoColor=white" alt="FFmpeg">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">
</p>

# 🎬 StorySync: Full-Stack Audio-Visual Synchronization & Rendering Engine

**A full-stack application that transforms text-based documentary/storytelling scripts into professional video segments using AI-powered image search and audio synchronization.**

It takes an audio recording and text input, segments the text using AI, aligns the text with audio via Whisper, automatically searches Google Images, and produces **perfectly lip-synced MP4 video segments** for each part.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Demo Flow](#-demo-flow)
- [Quick Start (Docker)](#-quick-start-docker)
- [Manual Setup (Development)](#-manual-setup-development)
- [API Keys](#-api-keys)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
- [Technical Details](#-technical-details)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Text Segmentation** | Segments documentary text into meaningful parts using Gemini API |
| 🎙️ **Whisper Audio Analysis** | Extracts word-level timestamps using OpenAI Whisper (GPU-accelerated) |
| 🔍 **Automatic Image Search** | Searches for contextually relevant images via Google Images for each segment |
| 🎬 **Video Generation** | Creates perfectly synchronized MP4 segments using FFmpeg |
| 🎯 **Frame-Aligned Sync** | 30 FPS frame alignment guarantees zero cumulative audio drift |
| 📱 **Modern Web UI** | Responsive, dark-mode interface built with React + Vite |
| 🐳 **Docker Ready** | Single-command deployment with NVIDIA GPU support |
| 💾 **Session Management** | Restores session state even after page reloads |

---

## 🏗️ Architecture

```text
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
│                   │  │ (Text)    │ │ (Audio→Text) │ │   │
│                   │  └───────────┘ └──────┬──────┘ │   │
│                   │                       │        │   │
│                   │  ┌───────────┐ ┌──────▼──────┐ │   │
│                   │  │  Serper   │ │  NVIDIA GPU │ │   │
│                   │  │ (Images)  │ │   (CUDA)   │ │   │
│                   │  └───────────┘ └─────────────┘ │   │
│                   │                                 │   │
│                   │  ┌─────────────────────────┐   │   │
│                   │  │  FFmpeg (Video Output)  │   │   │
│                   │  └─────────────────────────┘   │   │
│                   └────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 🎬 Demo Flow

### 1️⃣ Start Project
Upload your audio file (MP3/WAV) and documentary script. The AI automatically segments the text and aligns it with the audio using Whisper.

### 2️⃣ Review Timestamps
Check the AI's audio-text alignment. Edit and confirm any problematic matches.

### 3️⃣ Studio
Select one of the images retrieved from Google Images for each segment. Once selected, the video is generated and downloaded automatically.

### 4️⃣ Combine
Import the downloaded MP4 segments in sequence into your video editor (CapCut, DaVinci Resolve, etc.). The audio synchronization will be flawless.

---

## 🐳 Quick Start (Docker)

### Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Docker Engine** | 24.0+ | Latest Version |
| **RAM** | 4 GB | 8 GB+ |
| **Disk** | 10 GB | 20 GB+ |
| **GPU** | - | NVIDIA (CUDA 12.x) |

### With NVIDIA GPU (Recommended)

```bash
# 1. Install NVIDIA Container Toolkit (first time only)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# 2. Clone the project
git clone https://github.com/omerf-git/StorySync-Full-Stack-Audio-Visual-Synchronization-Rendering-Engine.git
cd StorySync-Full-Stack-Audio-Visual-Synchronization-Rendering-Engine

# 3. Setup API keys
cp backend/.env.example backend/.env
nano backend/.env  # Enter your API keys

# 4. Build and run
docker compose up -d --build

# 5. Open in browser
# http://localhost
```

### Without GPU (CPU Only)

```bash
# Follow the same steps, but use this command for step 4:
docker compose -f docker-compose.cpu.yml up -d --build
```

> ⚠️ Whisper runs ~3-5x slower in CPU mode, but all functions work smoothly.

---

## 🛠️ Manual Setup (Development)

### Requirements

- Python 3.10+
- Node.js 18+
- FFmpeg
- (Optional) NVIDIA GPU + CUDA

### Backend

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# PyTorch CUDA (if GPU is available)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# Setup API keys
cp .env.example .env
nano .env

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8005
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## 🔑 API Keys

This application requires 2 external API services:

| Service | Purpose | Free Tier | Where to Get |
|---------|---------|-----------|--------------|
| **Gemini API** | Text segmentation & translation | ✅ 1500 req/day | [Google AI Studio](https://aistudio.google.com/apikey) |
| **Serper API** | Google Images search | ✅ 2500 req/month | [serper.dev](https://serper.dev) |

Add your API keys to the `backend/.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key_here
SERPER_API_KEY=your_serper_api_key_here
```

---

## 📁 Project Structure

```
StorySync/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI endpoints & session management
│   │   └── services/
│   │       ├── text_to_json.py     # Text segmentation via Gemini AI
│   │       ├── audio_processing.py # Audio-text alignment via Whisper
│   │       ├── image_search.py     # Image search via Serper API
│   │       └── video_generation.py # Video generation via FFmpeg
│   ├── system_prompt.txt           # Gemini AI system instructions
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Example environment variables
│   └── .env                        # API keys (not tracked by git)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Main application component
│   │   ├── components/
│   │   │   ├── UploadView.jsx      # Audio & text upload view
│   │   │   ├── ReviewView.jsx      # Timestamp review view
│   │   │   └── StudioView.jsx      # Image selection & video generation view
│   │   ├── index.css               # Global styles (dark theme)
│   │   └── main.jsx                # React entry point
│   ├── package.json
│   └── vite.config.js              # Vite config & API proxy settings
│
├── Dockerfile                      # Multi-stage build (React + CUDA Python)
├── docker-compose.yml              # GPU supported deployment
├── docker-compose.cpu.yml          # CPU-only deployment
├── nginx.conf                      # Reverse proxy configuration
├── docker-entrypoint.sh            # Container startup script
├── .gitignore
├── .dockerignore
├── LICENSE
└── README.md
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Upload audio + text, start AI analysis |
| `GET` | `/api/session/{id}` | Get session details |
| `POST` | `/api/session/{id}/confirm` | Confirm timestamps |
| `GET` | `/api/session/{id}/images` | Get images for the current segment |
| `POST` | `/api/session/{id}/generate_video` | Generate video with the selected image |
| `POST` | `/api/session/{id}/next` | Skip to next segment |
| `POST` | `/api/session/{id}/prev` | Go back to previous segment |
| `POST` | `/api/session/{id}/next_keyword` | Search with a different keyword |
| `GET` | `/api/session/healthcheck` | Health check endpoint |

Detailed API documentation: `http://localhost:8005/docs` (Swagger UI)

---

## 🔧 Technical Details

### Audio-Video Synchronization

This application guarantees **zero cumulative drift** between video segments:

1. **Frame-Aligned Timestamps**: All timestamps are aligned to exact multiples of `1/30 seconds`.
2. **WAV Extraction**: Audio is extracted to PCM/WAV format first (sample-accurate cuts).
3. **Matched Duration**: Video and audio tracks are produced with exactly the same duration.
4. **Sequential Boundary Sync**: Boundary points of consecutive segments are perfectly aligned.

### Whisper Model

By default, the `small` model is used. For higher accuracy, `medium` or `large-v3` can be used (via the `model_name` parameter in `audio_processing.py`).

| Model | VRAM | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | ~1 GB | ⚡⚡⚡⚡ | ★★☆☆ |
| small | ~2 GB | ⚡⚡⚡ | ★★★☆ |
| medium | ~5 GB | ⚡⚡ | ★★★★ |
| large-v3 | ~10 GB | ⚡ | ★★★★★ |

### Watermark Filtering

Sources likely to contain watermarks (Getty Images, Shutterstock, iStock, etc.) are automatically filtered out from the image search results.

---

## 🐛 Troubleshooting

<details>
<summary><strong>Docker build takes too long</strong></summary>

The initial build may take ~10-15 minutes (PyTorch + CUDA download). Subsequent builds are much faster thanks to the Docker cache. You can run `docker compose build --no-cache` to force a complete rebuild.
</details>

<details>
<summary><strong>GPU is not detected</strong></summary>

```bash
# Check NVIDIA driver
nvidia-smi

# Is NVIDIA Container Toolkit installed?
dpkg -l | grep nvidia-container-toolkit

# Is the Docker runtime correct?
docker info | grep -i runtime
```
</details>

<details>
<summary><strong>"The source site for this image does not allow downloading" error</strong></summary>

Some websites block bot access. Select a different image or use the 🔑 button to try a different keyword.
</details>

<details>
<summary><strong>Whisper is running very slowly</strong></summary>

Whisper is slow in CPU mode. If you have an NVIDIA GPU, make sure you are using `docker-compose.yml` (the GPU version). Using a GPU provides a ~5-10x speed boost.
</details>

<details>
<summary><strong>Page refreshes return to the upload screen</strong></summary>

In-memory sessions are cleared if the backend server restarts. Make sure the server is running stably: `docker compose ps`
</details>

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">
  <sub>Built with ❤️ using Python, React, Whisper, Gemini & FFmpeg</sub>
</p>
