import json
import os
import re
import httpx
from dotenv import load_dotenv

load_dotenv()

ML_WORKER_URL = os.getenv("ML_WORKER_URL")
if not ML_WORKER_URL:
    print("WARNING: ML_WORKER_URL not set. Transcription will fail.")
    ML_WORKER_URL = "http://localhost:7860"


TRANSCRIPTION_ENDPOINT = f"{ML_WORKER_URL}/transcribe"


def convert_drive_link(url: str) -> str:
    match = re.search(r"/file/d/([a-zA-Z0-9_-]+)/", url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url

async def transcribe_video(video_input, output_filename="reports/transcript.json"):
    """
    Calls the external ML worker (Hugging Face Space) to transcribe the video.
    Saves the resulting JSON locally.
    """
    print(f"📝 Calling ML worker for transcription at {TRANSCRIPTION_ENDPOINT}...")
    

    video_url = convert_drive_link(video_input)

    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            response = await client.post(
                TRANSCRIPTION_ENDPOINT,
                json={"video_url": video_url}
            )
            response.raise_for_status()
            
            result_json = response.json()
            
        
            os.makedirs(os.path.dirname(output_filename), exist_ok=True)
            with open(output_filename, "w", encoding="utf-8") as f:
                json.dump(result_json, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Transcription successful, saved to {output_filename}")
            return output_filename

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP error calling ML worker: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        print(f"❌ Failed to call ML worker: {e}")
        raise