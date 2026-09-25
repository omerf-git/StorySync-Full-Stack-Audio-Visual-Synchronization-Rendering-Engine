import json
import argparse
import whisper
import difflib
import string
import re
import subprocess

def clean_text(text):
    """
    Removes punctuation and converts text to lowercase.
    Ensures more accurate matching.
    """
    text = text.lower()
    text = re.sub(f'[{re.escape(string.punctuation)}]', '', text)
    return text.strip()

def find_timestamp_for_text(sample_text, transcript_words):
    """
    Finds the best matching word group using a sliding window algorithm
    and returns the start/end times.
    """
    sample_words = [clean_text(w) for w in sample_text.split() if clean_text(w)]
    n = len(sample_words)
    if n == 0:
        return None, None, 0.0, "", []
    
    best_ratio = 0
    best_start = None
    best_end = None
    best_matched_words_raw = []
    
    sample_str = " ".join(sample_words)
    
    # Define sliding window range
    for i in range(len(transcript_words)):
        for j in range(i + max(1, n - 3), min(len(transcript_words) + 1, i + n + 4)):
            window = transcript_words[i:j]
            window_str = " ".join([clean_text(w['word']) for w in window if clean_text(w['word'])])
            
            # Find similarity ratio with difflib
            ratio = difflib.SequenceMatcher(None, window_str, sample_str).ratio()
            
            if ratio > best_ratio:
                best_ratio = ratio
                best_start = window[0]['start']
                best_end = window[-1]['end']
                best_matched_words_raw = window
                
    best_matched_text = " ".join([w['word'] for w in best_matched_words_raw])
    
    # Find mismatched words
    mismatched_words = []
    if best_matched_words_raw:
        whisper_clean_words = [clean_text(w['word']) for w in best_matched_words_raw if clean_text(w['word'])]
        matcher = difflib.SequenceMatcher(None, sample_words, whisper_clean_words)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag in ('replace', 'delete'):
                # Words in sample_text that do not match
                # Use split() to get original casing
                orig_words = sample_text.split()
                # Note: i1, i2 indices belong to sample_words (punctuation-free list).
                mismatched_words.extend(sample_words[i1:i2])
                
    return best_start, best_end, best_ratio, best_matched_text, mismatched_words

def get_transcript_words(audio_path, model_name="small"):
    print(f"Loading Whisper '{model_name}' model...")
    model = whisper.load_model(model_name)
    
    print(f"Analyzing audio file '{audio_path}' (this may take a while)...")
    result = model.transcribe(audio_path, word_timestamps=True)
    
    transcript_words = []
    for segment in result.get('segments', []):
        for word in segment.get('words', []):
            transcript_words.append({
                'word': word['word'],
                'start': word['start'],
                'end': word['end']
            })
    return transcript_words

def evaluate_timestamps(data, transcript_words):
    for item in data:
        sample_text = item.get('sample_text', '')
        if sample_text:
            start_time, end_time, match_ratio, matched_text, mismatched_words = find_timestamp_for_text(sample_text, transcript_words)
            
            item['match_ratio'] = round(match_ratio, 3) if match_ratio else 0.0
            
            if start_time is not None:
                item['start_time'] = round(start_time, 2)
                item['end_time'] = round(end_time, 2)
                item['matched_whisper_text'] = matched_text
                item['mismatched_words'] = mismatched_words
                
                if match_ratio >= 0.9:
                    item['match_status'] = 1
                elif match_ratio >= 0.6:
                    item['match_status'] = 2
                else:
                    item['match_status'] = 3
            else:
                item['match_status'] = 3
                item['matched_whisper_text'] = ""
                item['mismatched_words'] = [w for w in sample_text.split()]
                
    # --- GAP BRIDGING ---
    for i in range(len(data) - 1):
        current_item = data[i]
        next_item = data[i+1]
        
        if 'end_time' in current_item and 'start_time' in next_item:
            current_end = current_item['end_time']
            next_start = next_item['start_time']
            
            if current_end < next_start:
                mid_point = (current_end + next_start) / 2.0
                current_item['end_time'] = round(mid_point, 2)
                next_item['start_time'] = round(mid_point, 2)
    
    # --- FRAME-ALIGNED TIMESTAMP SNAPPING ---
    # Video 30 FPS → süre sadece 1/30 saniye (33.3ms) katlarından oluşabilir.
    # Eğer start_time ve end_time 1/30 katı değilse, video track sesten kısa/uzun kalır.
    # Bu fark her segmentte birikir ve CapCut'ta kayma oluşturur.
    # ÇÖZÜM: Tüm zaman damgalarını 1/30'un en yakın katına hizala.
    # Ardışık segmentler aynı sınır noktasını paylaştığı için boşluk/bindirme olmaz.
    fps = 30.0
    frame_dur = 1.0 / fps
    
    for i, item in enumerate(data):
        if 'start_time' in item and 'end_time' in item:
            # start_time'ı en yakın frame sınırına hizala
            snapped_start = round(item['start_time'] / frame_dur) * frame_dur
            snapped_start = round(snapped_start, 4)
            
            # end_time'ı en yakın frame sınırına hizala
            snapped_end = round(item['end_time'] / frame_dur) * frame_dur
            snapped_end = round(snapped_end, 4)
            
            # Sürenin en az 1 frame olduğundan emin ol
            if snapped_end <= snapped_start:
                snapped_end = snapped_start + frame_dur
            
            item['start_time'] = snapped_start
            item['end_time'] = snapped_end
    
    # Ardışık segmentlerin sınırlarını eşitle (snap sonrası oluşabilecek küçük farkları düzelt)
    for i in range(len(data) - 1):
        current_item = data[i]
        next_item = data[i+1]
        if 'end_time' in current_item and 'start_time' in next_item:
            # Bir öncekinin bitişini, bir sonrakinin başlangıcına eşitle
            next_item['start_time'] = current_item['end_time']
                
    return data

def get_audio_duration(audio_path):
    cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', audio_path]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        return float(result.stdout.strip())
    except Exception:
        return None

def process_audio_timestamps(data, audio_path, model_name="small", min_match=0.6):
    transcript_words = get_transcript_words(audio_path, model_name)
    data = evaluate_timestamps(data, transcript_words)
    
    # --- SON SEGMENTİ SES DOSYASININ SONUNA KADAR UZAT ---
    # Orijinal ses dosyasındaki son sessizliğin de (varsa) son videoya dahil edilmesi
    total_duration = get_audio_duration(audio_path)
    if total_duration and len(data) > 0:
        last_item = data[-1]
        if 'end_time' in last_item:
            fps = 30.0
            frame_dur = 1.0 / fps
            # Tam ses süresini yine video kare kuralına (1/30s) hizalıyoruz ki kayma olmasın
            snapped_duration = round(round(total_duration / frame_dur) * frame_dur, 4)
            # Eğer hesaplanan süre başlangıçtan büyükse son videonun bitişini uzat
            if snapped_duration > last_item.get('start_time', 0):
                last_item['end_time'] = snapped_duration
    
    for item in data:
        if item.get('match_ratio', 0) < min_match or item.get('match_status') == 3:
            error_message = f"\n\nERROR: Significant mismatch detected!\n" \
                          f"Text: '{item.get('sample_text')}'\n" \
                          f"Highest Match Ratio Found: {item.get('match_ratio', 0)*100:.1f}% (Required Minimum: {min_match*100:.1f}%)\n"
            raise ValueError(error_message)
    return data


def main():
    parser = argparse.ArgumentParser(description="Extract word timestamps from audio using Whisper and add to JSON.")
    parser.add_argument("--json", type=str, required=True, help="Input JSON file (e.g. output.json)")
    parser.add_argument("--audio", type=str, required=True, help="Input audio file (e.g. audio.mp3)")
    parser.add_argument("--output", type=str, default="output_with_timestamps.json", help="Output JSON file")
    parser.add_argument("--model", type=str, default="small", help="Whisper model to use (default: small)")
    parser.add_argument("--min-match", type=float, default=0.6, help="Minimum match ratio (0.0 to 1.0, default: 0.6)")
    
    args = parser.parse_args()
    
    print(f"Processing '{args.json}' file...")
    with open(args.json, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    data = process_audio_timestamps(data, args.audio, args.model, args.min_match)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        
    print(f"Process complete! Updated data saved to '{args.output}'.")

if __name__ == "__main__":
    main()
