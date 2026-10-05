# Backend Architecture & Development Guide

This document is a comprehensive developer and user guide that explains the backend architecture, directory structure, and instructions for integrating new features into the **StorySync** project.

## 1. Directory Structure
The backend is structured using a professional, modular FastAPI architecture.

```text
backend/
├── app/
│   ├── main.py              # Main controller handling all endpoints and session management.
│   └── services/            # Independent services containing the business logic.
│       ├── text_to_json.py      # Generates a JSON timeline from text using Gemini AI.
│       ├── audio_processing.py  # Extracts word-level timestamps from audio using Whisper AI.
│       ├── image_search.py      # Performs Google Image searches using the Serper API.
│       └── video_generation.py  # Combines images and audio with Ken Burns effects to output MP4s via FFmpeg & OpenCV.
├── .env                     # Environment variables (API keys, etc.)
├── requirements.txt         # Project dependencies
└── system_prompt.txt        # The main prompt file sent to Gemini AI
```

## 2. Development Logic and Principles

### 2.1 Service Layer
When adding or updating a feature, **never write the heavy logic directly inside `main.py`.**
- All intensive tasks such as image processing, audio processing, and external API calls must be implemented as functions inside the relevant Python file under `app/services/`.
- `main.py` should solely act as an Orchestrator (Controller) that calls these services.

### 2.2 Session Management
Currently, active sessions are stored in an In-Memory Python dictionary named `sessions` inside `main.py`.
- When a new session is initialized (Analyze phase), it starts with the state `confirmed: false`.
- If you plan to scale this project to support multiple concurrent users (multi-user architecture) in production, you must migrate the `sessions` dictionary to a persistent database such as **Redis**, **PostgreSQL**, or **SQLite**.

## 3. Pipeline Architecture
The system employs a **Two-Stage Initialization** logic. This structure is built for high error tolerance.

1. **`/api/analyze`**: The input text and audio are sent to the Gemini and Whisper services. The audio timestamps are calculated. However, even if mismatched (unrecognized) words are found, **the system does not crash**. Mismatched segments are reported to the frontend with a Status 3 (Critical Error).
2. **`/api/session/{id}/confirm`**: The frontend sends the corrected Whisper transcripts back to this endpoint, where a rapid re-matching is attempted. If no critical errors remain, the session is approved (`confirmed: true`).
3. Only confirmed sessions can utilize the `/images` (Image Search) and `/generate_video` (Video Generation) endpoints.

## 4. Tasks for New Feature Developers (TODO)
Potential starting points for adding new features to the project include:

- **Merging Videos:** Users might want to merge the individually generated video segments (`sample_1.mp4`, `sample_2.mp4`) into a single documentary file. To achieve this, write a new function inside `video_generation.py` utilizing FFmpeg's concat feature, and expose a `/api/session/{id}/merge` endpoint in `main.py`.
- **Asynchronous Processing:** Currently, the video generation process (`create_segment_from_url`) runs synchronously (blocking the response). In the future, this should be offloaded to the background using **Celery** or FastAPI's `BackgroundTasks`.
