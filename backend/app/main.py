import os
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

class VideoGenerationRequest(BaseModel):
    image_url: str
    ken_burns: bool = True
    zoom_direction: str = "in"

class ConfirmSessionRequest(BaseModel):
    json_data: list
    transcript_words: list

@app.post("/api/analyze")
def analyze_audio(
    text: str = Form(...),
    system_prompt_path: str = Form("system_prompt.txt"),
    audio: UploadFile = File(...)
):
    try:
        # 1. Generate JSON from text
        if not os.path.exists(system_prompt_path):
            raise HTTPException(status_code=400, detail=f"System prompt file '{system_prompt_path}' not found.")
        
        json_data = generate_json_from_text(system_prompt_path, text)
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
            "confirmed": False
        }

        return {
            "status": "success",
            "session_id": session_id,
            "total_segments": len(json_data),
            "json_data": json_data,
            "transcript_words": transcript_words,
            "message": "Analysis complete. Please confirm timestamps."
        }

    except Exception as e:
        logger.error(f"Error in /api/analyze: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during text/audio analysis. Please check the logs.")

@app.post("/api/session/{session_id}/confirm")
def confirm_session(session_id: str, req: ConfirmSessionRequest):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = sessions[session_id]
    
    # Re-evaluate with potentially user-edited transcript words or JSON data
    updated_json = evaluate_timestamps(req.json_data, req.transcript_words)
    
    # Check if there are any critical errors remaining
    has_critical_error = any(item.get("match_status") == 3 for item in updated_json)
    
    if has_critical_error:
        return {
            "status": "review_needed",
            "json_data": updated_json,
            "transcript_words": req.transcript_words,
            "message": "There are still segments with critical errors (Status 3)."
        }
        
    # All good, save and mark as confirmed
    session["json_data"] = updated_json
    session["transcript_words"] = req.transcript_words
    session["confirmed"] = True
    
    return {
        "status": "success",
        "message": "Timestamps confirmed. Session is ready."
    }

@app.get("/api/session/{session_id}")
def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = sessions[session_id]
    return {
        "status": "success",
        "session_id": session_id,
        "json_data": session["json_data"],
        "transcript_words": session["transcript_words"],
        "confirmed": session.get("confirmed", False)
    }



@app.get("/api/session/{session_id}/images")
def get_session_images(session_id: str, more: bool = False):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = sessions[session_id]
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

        return {
            "status": "success",
            "index": idx,
            "keyword_used": keyword_used,
            "english_translation": english_trans,
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
        
    try:
        images = search_images(keyword)
        # Cache the result
        session["image_cache"][idx] = images
        session["image_offset"][idx] = 0
        
        paginated_images = images[0:4]
        
        return {
            "status": "success",
            "index": idx,
            "keyword_used": keyword,
            "english_translation": english_trans,
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
def next_segment(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = sessions[session_id]
    if session["current_index"] < len(session["json_data"]) - 1:
        session["current_index"] += 1
    else:
        return {"status": "success", "message": "Already at the last segment", "index": session["current_index"]}
        
    return get_session_images(session_id)


@app.post("/api/session/{session_id}/prev")
def prev_segment(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session = sessions[session_id]
    if session["current_index"] > 0:
        session["current_index"] -= 1
    else:
        return {"status": "success", "message": "Already at the first segment", "index": session["current_index"]}
        
    return get_session_images(session_id)

@app.post("/api/session/{session_id}/next_keyword")
def next_keyword(session_id: str):
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
        
    return get_session_images(session_id)
