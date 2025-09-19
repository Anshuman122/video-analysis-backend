import json
from datetime import timedelta
import whisperx
import os
import re
import requests

# ----------------------
# Helper: Convert seconds to HH:MM:SS
# ----------------------
def seconds_to_time(s):
    return str(timedelta(seconds=int(s)))

# ----------------------
# Helper: Save transcript to JSON
# ----------------------
def save_transcript(filename, result):
    output = [
        {
            "start": seconds_to_time(seg["start"]),
            "end": seconds_to_time(seg["end"]),
            "text": seg["text"]
        }
        for seg in result["segments"]
    ]
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    return filename

# ----------------------
# Drive Link Converter
# ----------------------
def convert_drive_link(url: str) -> str:
    match = re.search(r"/file/d/([a-zA-Z0-9_-]+)/", url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url

# ----------------------
# Downloader
# ----------------------
def download_from_url(url, filename="temp_video.mp4"):
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(filename, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    return filename

# ----------------------
# Load WhisperX model once (lazy load inside function for compare.py)
# ----------------------
model = None
def get_model():
    global _model
    if model is None:
        model = whisperx.load_model("base", device="cpu", compute_type="int8")
    return model

# ----------------------
# Main function
# ----------------------
def transcribe_video(video_input, output_filename="reports/transcript.json"):
    import whisperx  # ensure fresh import

    # Load the model **inside the function**
    model = whisperx.load_model("base", device="cpu", compute_type="int8")
    if model is None:
        raise RuntimeError("❌ Failed to load WhisperX model.")

    # ... rest of your existing code ...
    print("📝 Transcribing video...")
    result = model.transcribe(video_input)  # or the downloaded file
    save_transcript(output_filename, result)
    return output_filename