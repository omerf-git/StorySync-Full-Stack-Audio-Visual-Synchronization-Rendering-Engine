import os
import time
import uuid
import tempfile
import shutil
from typing import Optional, List
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, Response, RedirectResponse

from app.services.text_to_json import generate_json_from_text, setup_gemini_api
from app.services.audio_processing import get_transcript_words, evaluate_timestamps
from app.services.image_search import search_images
from app.services.video_generation import create_segment_from_url

# Setup environment / API keys
from dotenv import load_dotenv
import logging

load_dotenv()

# Setup Logging
# Default log level is INFO. For detailed developer logs, add LOG_LEVEL=DEBUG to the .env file.
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

# 1. We set the root log level to WARNING to silence unnecessary logs from 3rd party libraries (urllib3, asyncio, etc.)
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
)

# 2. Set the log level for our own application ("app").
logging.getLogger("app").setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

# We need to setup gemini at startup
setup_gemini_api()

app = FastAPI(title="Google Images to Video Backend")

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")

@app.get("/api/session/healthcheck")
def healthcheck():
    return {"status": "ok"}

# In-memory session store
# sessions[session_id] = {
#     "json_data": list,
#     "current_index": int,
#     "audio_path": str,
#     "image_cache": dict,
#     "transcript_words": list,
#     "confirmed": bool
# }
sessions = {}

def cleanup_old_sessions():
    """Removes sessions inactive for more than 2 hours and deletes their files."""
    current_time = time.time()
    expired = []
    for sid, s in sessions.items():
        if current_time - s.get("last_activity", current_time) > 2 * 3600:
            expired.append(sid)
            
    for sid in expired:
        audio_path = sessions[sid].get("audio_path")
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass
        del sessions[sid]
        logger.info(f"Session {sid} deleted due to 2 hours of inactivity.")

class VideoGenerationRequest(BaseModel):
    image_url: str
    ken_burns: bool = True
    zoom_direction: str = "in"

@app.post("/api/analyze")
def analyze_audio(
    text: str = Form(...),
    system_prompt_path: str = Form("system_prompt.txt"),
    global_context: str = Form(""),
    audio: UploadFile = File(...)
):
    cleanup_old_sessions()
    try:
        # 1. Generate JSON from text
        if not os.path.exists(system_prompt_path):
            raise HTTPException(status_code=400, detail=f"System prompt file '{system_prompt_path}' not found.")
        
        json_data = generate_json_from_text(system_prompt_path, text, global_context)
        if not json_data:
            raise HTTPException(status_code=500, detail="Failed to generate JSON from text.")

        # 2. Save audio to a temporary file for the session
        temp_dir = tempfile.gettempdir()
        session_id = uuid.uuid4().hex
        audio_ext = os.path.splitext(audio.filename)[1] or ".mp3"
        audio_path = os.path.join(temp_dir, f"session_{session_id}_audio{audio_ext}")
        
        with open(audio_path, "wb") as buffer:
            shutil.copyfileobj(audio.file, buffer)

        # 3. Analyze audio and get transcript words
        transcript_words = get_transcript_words(audio_path)

        # 4. Evaluate timestamps
        json_data = evaluate_timestamps(json_data, transcript_words)

        # 5. Store in session (Unconfirmed state)
        sessions[session_id] = {
            "json_data": json_data,
            "current_index": 0,
            "audio_path": audio_path,
            "image_cache": {},
            "image_offset": {},
            "keyword_index": {},
            "transcript_words": transcript_words,
            "confirmed": True,
            "last_activity": time.time()
        }

        return {
            "status": "success",
            "session_id": session_id,
            "total_segments": len(json_data),
            "json_data": json_data,
            "transcript_words": transcript_words,
            "message": "Analysis complete."
        }

    except Exception as e:
        logger.error(f"Error in /api/analyze: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during text/audio analysis. Please check the logs.")

@app.get("/api/session/{session_id}")
def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = sessions[session_id]
    session["last_activity"] = time.time()
    return {
        "status": "success",
        "session_id": session_id,
        "json_data": session["json_data"],
        "transcript_words": session["transcript_words"],
        "confirmed": session.get("confirmed", False)
    }



def _prefetch_next_segment(session_id: str, next_idx: int):
    """Background task: search images for the next segment and cache them."""
    if session_id not in sessions:
        return
    
    session = sessions[session_id]
    json_data = session["json_data"]
    
    # Don't prefetch if already cached or out of bounds
    if next_idx >= len(json_data) or next_idx in session["image_cache"]:
        return
    
    next_item = json_data[next_idx]
    
    # Use the first keyword (index 0) for prefetch
    if "search_keywords" in next_item and isinstance(next_item["search_keywords"], list) and len(next_item["search_keywords"]) > 0:
        keyword = next_item["search_keywords"][0]
    else:
        keyword = next_item.get("sample_image") or next_item.get("english_translation") or next_item.get("english_sum") or next_item.get("sample_text", "")[:30]
    
    try:
        images = search_images(keyword)
        # Only cache if session still exists and index is still not cached
        if session_id in sessions and next_idx not in sessions[session_id]["image_cache"]:
            sessions[session_id]["image_cache"][next_idx] = images
            sessions[session_id]["image_offset"][next_idx] = 0
            logger.info(f"Prefetched {len(images)} images for segment {next_idx + 1} (keyword: '{keyword}')")
    except Exception as e:
        logger.warning(f"Prefetch failed for segment {next_idx + 1}: {e}")


@app.get("/api/session/{session_id}/images")
def get_session_images(session_id: str, background_tasks: BackgroundTasks, more: bool = False):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = sessions[session_id]
    session["last_activity"] = time.time()
    if not session.get("confirmed", False):
        raise HTTPException(status_code=400, detail="Session timestamps have not been confirmed yet.")
        
    idx = session["current_index"]
    json_data = session["json_data"]
    
    if idx >= len(json_data):
        return {
            "status": "completed", 
            "message": "Videos generated successfully for all segments."
        }
        
    if idx < 0:
        raise HTTPException(status_code=400, detail="Current index out of bounds")
        
    # Check cache first
    if idx in session["image_cache"]:
        cached_images = session["image_cache"][idx]
        current_offset = session["image_offset"].get(idx, 0)
        
        if more:
            current_offset += 4
            if current_offset >= len(cached_images):
                current_offset = 0 # Loop back to start if we run out
            session["image_offset"][idx] = current_offset
            
        paginated_images = cached_images[current_offset : current_offset + 4]
        
        # Backward compatibility and new keyword logic
        current_item = json_data[idx]
        keyword_idx = session.setdefault("keyword_index", {}).get(idx, 0)
        
        if "search_keywords" in current_item and isinstance(current_item["search_keywords"], list) and len(current_item["search_keywords"]) > 0:
            keyword_list = current_item["search_keywords"]
            keyword_used = keyword_list[keyword_idx % len(keyword_list)]
        else:
            keyword_used = current_item.get("sample_image") or current_item.get("english_translation") or current_item.get("english_sum", "")
            
        english_trans = current_item.get("english_translation", current_item.get("english_sum", ""))
        turkish_trans = current_item.get("turkish_translation", current_item.get("turkish_sum", ""))

        # Prefetch next segment in the background
        if idx + 1 < len(json_data):
            background_tasks.add_task(_prefetch_next_segment, session_id, idx + 1)

        return {
            "status": "success",
            "index": idx,
            "keyword_used": keyword_used,
            "english_translation": english_trans,
            "turkish_translation": turkish_trans,
            "images": paginated_images,
            "total_cached": len(cached_images)
        }
        
    # Not in cache, perform search
    current_item = json_data[idx]
    keyword_idx = session.setdefault("keyword_index", {}).get(idx, 0)
    
    if "search_keywords" in current_item and isinstance(current_item["search_keywords"], list) and len(current_item["search_keywords"]) > 0:
        keyword_list = current_item["search_keywords"]
        keyword = keyword_list[keyword_idx % len(keyword_list)]
    else:
        keyword = current_item.get("sample_image") or current_item.get("english_translation") or current_item.get("english_sum") or current_item.get("sample_text", "")[:30]
        
    english_trans = current_item.get("english_translation", current_item.get("english_sum", ""))
    turkish_trans = current_item.get("turkish_translation", current_item.get("turkish_sum", ""))
        
    try:
        images = search_images(keyword)
        # Cache the result
        session["image_cache"][idx] = images
        session["image_offset"][idx] = 0
        
        paginated_images = images[0:4]
        
        # Prefetch next segment in the background
        if idx + 1 < len(json_data):
            background_tasks.add_task(_prefetch_next_segment, session_id, idx + 1)
        
        return {
            "status": "success",
            "index": idx,
            "keyword_used": keyword,
            "english_translation": english_trans,
            "turkish_translation": turkish_trans,
            "images": paginated_images,
            "total_cached": len(images)
        }
    except Exception as e:
        logger.error(f"Error in /api/session/.../images: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="A server error occurred while searching for images.")


@app.post("/api/session/{session_id}/generate_video")
def generate_video(session_id: str, req: VideoGenerationRequest):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = sessions[session_id]
    if not session.get("confirmed", False):
        raise HTTPException(status_code=400, detail="Session timestamps have not been confirmed yet.")
        
    idx = session["current_index"]
    json_data = session["json_data"]
    audio_path = session["audio_path"]
    
    if idx < 0 or idx >= len(json_data):
        raise HTTPException(status_code=400, detail="Current index out of bounds")
        
    current_item = json_data[idx]
    
    try:
        video_bytes = create_segment_from_url(
            json_item=current_item,
            audio_path=audio_path,
            image_url=req.image_url,
            ken_burns=False, # Disabled (user request: only static image + audio)
            zoom_direction=req.zoom_direction
        )
        
        # Increment index on successful generation
        session["current_index"] += 1
        
        return Response(
            content=video_bytes, 
            media_type="video/mp4",
            headers={
                "Content-Disposition": f"attachment; filename=sample_{idx+1}.mp4"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in /api/session/.../generate_video: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during video generation.")


@app.post("/api/session/{session_id}/next")
def next_segment(session_id: str, background_tasks: BackgroundTasks):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = sessions[session_id]
    if session["current_index"] < len(session["json_data"]):
        session["current_index"] += 1
        
    return get_session_images(session_id, background_tasks=background_tasks)


@app.post("/api/session/{session_id}/prev")
def prev_segment(session_id: str, background_tasks: BackgroundTasks):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = sessions[session_id]
    if session["current_index"] > 0:
        session["current_index"] -= 1
        
    return get_session_images(session_id, background_tasks=background_tasks)

@app.post("/api/session/{session_id}/next_keyword")
def next_keyword(session_id: str, background_tasks: BackgroundTasks):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = sessions[session_id]
    idx = session["current_index"]
    
    # Increment keyword index
    current_kw_idx = session.setdefault("keyword_index", {}).get(idx, 0)
    session["keyword_index"][idx] = current_kw_idx + 1
    
    # Reset offset and cache for this index to force fresh search
    session["image_offset"][idx] = 0
    if idx in session["image_cache"]:
        del session["image_cache"][idx]
        
    return get_session_images(session_id, background_tasks=background_tasks)


@app.delete("/api/session/{session_id}")
def delete_session(session_id: str):
    if session_id in sessions:
        audio_path = sessions[session_id].get("audio_path")
        if audio_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass
        del sessions[session_id]
        logger.info(f"Session {session_id} explicitly deleted by user.")
    return {"status": "success", "message": "Session deleted."}
