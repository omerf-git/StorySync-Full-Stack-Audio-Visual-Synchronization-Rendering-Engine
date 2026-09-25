import os
import cv2
import subprocess
import tempfile
import uuid
import math
import numpy as np

def _get_focal_point(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return (0.5, 0.5)
    
    # Find the most intense (brightest) area by converting to grayscale and blurring
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (0, 0), sigmaX=30, sigmaY=30)
    _, _, _, max_loc = cv2.minMaxLoc(gray)
    
    h, w = img.shape[:2]
    # Blend 70% brightest point with 30% center coordinate to avoid extreme edges
    target_x = (0.7 * max_loc[0]) + (0.3 * (w / 2.0))
    target_y = (0.7 * max_loc[1]) + (0.3 * (h / 2.0))
    
    return (target_x / w, target_y / h)

def _map_focal_to_canvas(img_path, output_res):
    img = cv2.imread(img_path)
    if img is None:
        return (output_res[0] / 2.0, output_res[1] / 2.0)

    h0, w0 = img.shape[:2]
    out_w, out_h = output_res
    fx_n, fy_n = _get_focal_point(img_path)

    scale = max(out_w / w0, out_h / h0)
    rw = w0 * scale
    rh = h0 * scale
    ox = (rw - out_w) / 2.0
    oy = (rh - out_h) / 2.0

    fx = (fx_n * rw) - ox
    fy = (fy_n * rh) - oy
    fx = max(0.0, min(out_w, fx))
    fy = max(0.0, min(out_h, fy))
    return (fx, fy)

def _build_segment_cpu(
    ffmpeg_bin, img_path, segment_path, output_res, fps,
    img_duration, target_zoom, focal_canvas, reverse, fade_duration
):
    out_w, out_h = output_res
    frames_per_image = max(int(round(img_duration * fps)), 1)
    
    img = cv2.imread(img_path)
    if img is None:
        raise RuntimeError(f"Could not read image: {img_path}")
    
    h0, w0 = img.shape[:2]
    scale = max(out_w / w0, out_h / h0)
    rw = int(round(w0 * scale))
    rh = int(round(h0 * scale))
    
    img_rsz = cv2.resize(img, (rw, rh), interpolation=cv2.INTER_LANCZOS4)
    
    cmd = [
        ffmpeg_bin, "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
        "-s", f"{out_w}x{out_h}", "-r", str(fps), "-i", "-",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-pix_fmt", "yuv420p", segment_path,
    ]
    
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    
    fade_frames = int(round(fade_duration * fps)) if fade_duration > 0 else 0
    tx, ty = focal_canvas
    
    for i in range(frames_per_image):
        p = i / max(frames_per_image - 1, 1)
        smooth_p = 0.5 - 0.5 * math.cos(math.pi * p)
        
        current_zoom = 1.0 + (target_zoom - 1.0) * (1.0 - smooth_p if reverse else smooth_p)
        
        crop_w = out_w / current_zoom
        crop_h = out_h / current_zoom
        max_x = rw - crop_w
        max_y = rh - crop_h
        
        cur_cx = (rw / 2.0) + (tx - (rw / 2.0)) * (current_zoom - 1.0) / (target_zoom - 1.0) if target_zoom > 1.0 else rw / 2.0
        cur_cy = (rh / 2.0) + (ty - (rh / 2.0)) * (current_zoom - 1.0) / (target_zoom - 1.0) if target_zoom > 1.0 else rh / 2.0
        
        crop_x = max(0.0, min(max_x, cur_cx - crop_w / 2.0))
        crop_y = max(0.0, min(max_y, cur_cy - crop_h / 2.0))
        
        scale_x = out_w / crop_w
        scale_y = out_h / crop_h
        
        M = np.array([
            [scale_x, 0, -crop_x * scale_x],
            [0, scale_y, -crop_y * scale_y]
        ], dtype=np.float32)
        
        frame = cv2.warpAffine(img_rsz, M, (out_w, out_h), flags=cv2.INTER_LINEAR)
        
        if fade_frames > 0:
            if i < fade_frames:
                frame = (frame * (i / float(fade_frames))).astype(np.uint8)
            elif i > frames_per_image - fade_frames:
                frame = (frame * ((frames_per_image - i) / float(fade_frames))).astype(np.uint8)
                
        try:
            proc.stdin.write(frame.tobytes())
        except BrokenPipeError:
            err = proc.stderr.read().decode()
            raise RuntimeError(f"FFmpeg crashed early (Broken Pipe). FFmpeg error:\n{err}")
            
    proc.stdin.close()
    proc.wait()
    if proc.returncode != 0:
        err = proc.stderr.read().decode()
        raise RuntimeError(f"Failed to create segment ({img_path}):\n{err[-1600:]}")


def create_segment_video(json_item, audio_path, image_path, ken_burns=False, zoom_direction="in"):
    """
    Uses the start_time and end_time properties of the specified json element
    to trim the corresponding section from the audio file and combine it with the given image to create a video.
    
    Parameters:
        json_item (dict): Object containing 'start_time' and 'end_time' keys.
        audio_path (str): Path of the original audio file.
        image_path (str): Path of the image to be shown in the background.
        ken_burns (bool): Whether to apply the Ken Burns effect (default: False).
        zoom_direction (str): Direction of the effect ("in" or "out"). (default: "in").
        
    Returns:
        bytes: Byte data of the generated video.
    """
    start_time = json_item.get('start_time')
    end_time = json_item.get('end_time')
    
    if start_time is None or end_time is None:
        raise ValueError("'start_time' or 'end_time' not found in JSON item.")
        
    duration = end_time - start_time
    if duration <= 0:
        raise ValueError("Calculated duration must be greater than 0.")
        
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
        
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Use unique names to avoid temporary file conflicts
    temp_dir = tempfile.gettempdir()
    temp_video_filename = f"temp_video_{uuid.uuid4().hex[:8]}.mp4"
    temp_video_path = os.path.join(temp_dir, temp_video_filename)
    temp_out_filename = f"temp_out_{uuid.uuid4().hex[:8]}.mp4"
    temp_out_path = os.path.join(temp_dir, temp_out_filename)
    
    try:
        # KESİN ÇÖZÜM: Ken burns'ü fonksiyonun en tepesinde her ihtimale karşı False yapıyoruz
        ken_burns = False
        
        if ken_burns:
            # Determine image dimensions
            img = cv2.imread(image_path)
            if img is not None:
                w = img.shape[1]
                h = img.shape[0]
                # libx264 requires dimensions to be divisible by 2
                w = w if w % 2 == 0 else w - 1
                h = h if h % 2 == 0 else h - 1
                output_res = (w, h)
            else:
                output_res = (1080, 1920) # Default if image unreadable
                
            # Use target zoom ratio (min 1.0, max 1.25)
            target_zoom = min(1.0 + (duration * 0.045), 1.25)
            focal_canvas = _map_focal_to_canvas(image_path, output_res)
            
            # Check zoom direction ('out' sets reverse to True)
            reverse = (zoom_direction.lower() == "out")
            
            # Create silent temporary video with Ken Burns effect
            _build_segment_cpu(
                ffmpeg_bin='ffmpeg',
                img_path=image_path,
                segment_path=temp_video_path,
                output_res=output_res,
                fps=30,
                img_duration=duration,
                target_zoom=target_zoom,
                focal_canvas=focal_canvas,
                reverse=reverse,
                fade_duration=0.0
            )
            
            # Combine generated silent video with trimmed audio
            cmd = [
                'ffmpeg', '-y',
                '-ss', str(start_time),
                '-t', str(duration),
                '-i', audio_path,
                '-i', temp_video_path,
                '-map', '1:v',
                '-map', '0:a',
                '-c:v', 'copy', # Video is already encoded as libx264, no need to re-encode
                '-c:a', 'aac',
                '-b:a', '192k',
                temp_out_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg audio merge error:\n{result.stderr[-1000:]}")
            
        else:
            # ── Frame-Aligned Duration ──
            # audio_processing.py'de tüm start_time/end_time değerleri 1/30 katına
            # hizalandığı için duration zaten tam bir frame katıdır.
            # round() ile küçük kayan nokta hatalarını düzeltiyoruz.
            exact_frames = round(duration * 30)
            aligned_duration = exact_frames / 30.0
            
            # ── ADIM 1: Sesi frame-aligned sürede WAV'a çıkar ──
            temp_wav_filename = f"temp_audio_{uuid.uuid4().hex[:8]}.wav"
            temp_wav_path = os.path.join(temp_dir, temp_wav_filename)
            
            wav_cmd = [
                'ffmpeg', '-y',
                '-i', audio_path,
                '-ss', str(start_time),
                '-t', str(aligned_duration),
                '-acodec', 'pcm_s16le',
                '-ar', '44100',
                '-ac', '2',
                temp_wav_path
            ]
            try:
                result = subprocess.run(wav_cmd, capture_output=True, text=True, timeout=15)
                if result.returncode != 0:
                    raise RuntimeError(f"FFmpeg WAV extraction error:\n{result.stderr[-1000:]}")
            except subprocess.TimeoutExpired:
                subprocess.run(['pkill', '-f', temp_wav_path])
                raise RuntimeError("Ses çıkarma işlemi zaman aşımına uğradı.")
            
            # ── ADIM 2: WAV + sabit görsel → MP4 ──
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-framerate', '30',
                '-i', image_path,
                '-i', temp_wav_path,
                '-map', '0:v',
                '-map', '1:a',
                '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '18',
                '-pix_fmt', 'yuv420p',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-frames:v', str(exact_frames),
                '-t', str(aligned_duration),
                temp_out_path
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode != 0:
                    raise RuntimeError(f"FFmpeg (Static Image) error:\n{result.stderr[-1000:]}")
            except subprocess.TimeoutExpired:
                proc_kill = subprocess.run(['pkill', '-f', temp_out_path]) # Try to clean up stuck process
                raise RuntimeError("FFmpeg işlemi çok uzun sürdü ve zaman aşımına uğradı. Görsel formatı desteklenmiyor olabilir.")
            
            # WAV geçici dosyasını temizle
            if os.path.exists(temp_wav_path):
                os.remove(temp_wav_path)
            
    finally:
        # Clean up temporary video file if created to avoid inflating disk space
        if os.path.exists(temp_video_path):
            os.remove(temp_video_path)
            
    if not os.path.exists(temp_out_path):
        raise RuntimeError("Video generation failed, temporary output file not found.")
        
    with open(temp_out_path, "rb") as f:
        video_bytes = f.read()
        
    # Clean up output file
    os.remove(temp_out_path)
            
    return video_bytes

def create_segment_from_url(json_item, audio_path, image_url, ken_burns=False, zoom_direction="in"):
    import requests
    temp_dir = tempfile.gettempdir()
    temp_image_filename = f"temp_image_{uuid.uuid4().hex[:8]}.jpg"
    temp_image_path = os.path.join(temp_dir, temp_image_filename)
    
    try:
        # Download image
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
        }
        try:
            response = requests.get(image_url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Bu görselin kaynak sitesi indirmeye izin vermiyor (Güvenlik engeli). Lütfen farklı bir görsel seçin. Detay: {str(e)}")
            
        with open(temp_image_path, "wb") as f:
            f.write(response.content)
            
        # Create video
        return create_segment_video(
            json_item=json_item, 
            audio_path=audio_path, 
            image_path=temp_image_path, 
            ken_burns=ken_burns, 
            zoom_direction=zoom_direction
        )
    finally:
        # Clean up temporary image
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)

# if __name__ == "__main__":
#     import json
    
#     # Test block (To be commented out later)
#     try:
#         print("Reading JSON data...")
#         with open("output_with_timestamps.json", "r", encoding="utf-8") as f:
#             data = json.load(f)
            
#         # Element at index 1 (0th index is the first element)
#         first_item = data[0] 
        
#         print(f"Starting test. Processing audio range: {first_item.get('start_time')}s - {first_item.get('end_time')}s")
        
#         video_bytes = create_segment_video(
#             json_item=first_item, 
#             audio_path="leaonidasilk4.mp3", 
#             image_path="downloaded_images/sample1_image3.jpg", 
#             ken_burns=True,
#             zoom_direction="in"
#         )
        
#         output_path = "test_output.mp4"
#         with open(output_path, "wb") as f:
#             f.write(video_bytes)
            
#         print(f"Success! Video received as bytes and saved to '{output_path}'.")
        
#     except Exception as e:
#         print(f"Error occurred: {e}")
