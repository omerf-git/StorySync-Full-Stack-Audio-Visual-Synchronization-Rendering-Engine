# Frontend Usage & API Integration Guide

Welcome to the frontend development guide for the **Google Images to Video** backend API. This guide outlines how to consume the REST API to build a reliable and robust frontend client.

## Overview
The API is built with FastAPI and follows a session-based architecture. A typical generation pipeline consists of 4 main phases:
1. **Analysis (`/api/analyze`)**: Uploading the audio and script to generate a JSON timeline and evaluate Whisper word alignments.
2. **Review & Confirm (`/api/session/{id}/confirm`)**: Presenting any mismatched words to the user for correction and confirming the session.
3. **Image Selection (`/api/session/{id}/images`)**: Iterating through the JSON segments and presenting top Google Images to the user for the active segment.
4. **Video Generation (`/api/session/{id}/generate_video`)**: Turning the selected image and its corresponding audio clip into a Ken Burns video segment.

---

## 1. Starting a New Session
**Endpoint:** `POST /api/analyze` (Multipart Form Data)

When the user wants to start a new project, send the script and the audio file here.

**Request Body:**
- `text` (string): The raw script text.
- `audio` (file): The voiceover file (e.g., MP3/WAV).
- `system_prompt_path` (string, optional): Default is `system_prompt.txt`.

**Response (200 OK):**
```json
{
  "status": "success",
  "session_id": "c62b48a...",
  "total_segments": 15,
  "json_data": [
    {
      "sample_num": 1,
      "sample_text": "...",
      "sample_image": "...",
      "match_status": 1,
      "match_ratio": 0.95,
      "start_time": 0.0,
      "end_time": 5.2,
      "matched_whisper_text": "...",
      "mismatched_words": []
    }
  ],
  "transcript_words": [ ... ]
}
```

### Understanding `match_status`:
- **`1` (Perfect):** >= 90% match. You can safely proceed.
- **`2` (Minor Error):** 60% - 89% match. You should highlight the `mismatched_words` in the UI to let the user know Whisper misheard a word, but the pipeline won't be blocked.
- **`3` (Critical Error):** < 60% match. The pipeline **IS BLOCKED**. The user must edit the transcript before proceeding.

---

## 2. Review and Confirmation
**Endpoint:** `POST /api/session/{session_id}/confirm` (JSON)

If there are any `match_status = 3` items, you must let the user fix the transcription. Send the edited `transcript_words` and `json_data` back to this endpoint.

**Request Body:**
```json
{
  "json_data": [ ... ],
  "transcript_words": [ ... ]
}
```

**Response:**
If the edits successfully resolved the critical errors:
```json
{
  "status": "success",
  "message": "Timestamps confirmed. Session is ready."
}
```
If errors still remain, the API will return a 200 OK but with `status: "review_needed"` and the updated JSON data.

> [!IMPORTANT]
> None of the endpoints below will work until a session is successfully confirmed!

---

## 3. Fetching Images for the Current Segment
**Endpoint:** `GET /api/session/{session_id}/images`

Once confirmed, use this to get the top 5 image suggestions for the **current active segment**. The backend keeps track of the current segment index internally.

**Response:**
```json
{
  "status": "success",
  "index": 0,
  "keyword_used": "Apple iPhone 15",
  "images": [
    {
      "title": "...",
      "imageUrl": "https://...",
      "imageWidth": 1920,
      "imageHeight": 1080,
      "source": "..."
    }
  ]
}
```

---

## 4. Generating the Video Segment
**Endpoint:** `POST /api/session/{session_id}/generate_video`

When the user selects an image from the list, send its URL to this endpoint. The backend will download it, apply a Ken Burns effect, merge it with the audio segment, and return the raw MP4 file.

**Request Body:**
```json
{
  "image_url": "https://...",
  "ken_burns": true,
  "zoom_direction": "in"
}
```

**Response:**
- `Content-Type: video/mp4` (Raw video bytes).
- **Side Effect:** The backend automatically increments the `current_index` after a successful generation. So calling `/images` again will fetch images for the next segment.

---

## 5. Navigation Commands
If the user wants to skip a segment or go back to re-generate an older one, use these endpoints:

- **`POST /api/session/{session_id}/next`**
- **`POST /api/session/{session_id}/prev`**

Both endpoints return the image list for the new active index (same format as `/images`).

> [!TIP]
> Since the backend caches image search results, calling `/prev` will return instantly without consuming a Serper API request.
