import os
import json
import asyncio
import sys
from datetime import datetime

from Backend.transcription import transcribe_video, convert_drive_link 
from Backend.tweleve_labs_visualization import analyze_video
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv


load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not set. LLM features disabled.")

print(f"✅ Using google-generativeai version: {genai.__version__}")

model = None
if API_KEY:
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        print("WARNING: Could not initialize Gemini model:", e)

async def run_transcription(video_source: str):
    """
    Run transcription by calling the ML Worker API.
    Returns transcript segments.
    """
    transcript_file = os.path.join("reports", "transcript.json")
    
    
    path = await transcribe_video(video_source, transcript_file) 
    
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def run_visual_analysis(video_source: str):
    """Run Twelve Labs visual analysis and return visual segments"""
    result = analyze_video(video_source)  
    visual_file = os.path.join("reports", "visual.json")
    with open(visual_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    return result.get("scenes", [])


def run_llm(prompt: str) -> dict:

    if model is None:
        return {"raw_output": "LLM not configured; cannot process."}

    response = model.generate_content(prompt)

    try:
        text = response.text.strip()
        # Clean code fences if returned
        if text.startswith("```"):
            text = text.strip("`").replace("json", "", 1).strip()
        return json.loads(text)
    except Exception:
        return {"raw_output": response.text or "LLM returned nothing"}


def build_prompt(transcription, visual):
    return f"""
You are analyzing a video.

- Transcription (spoken words): {json.dumps(transcription, indent=2)}
- Visual descriptions: {json.dumps(visual, indent=2)}

Tasks:
1. Identify mismatches between what is spoken and what is shown, with timestamps.
2. Identify any spelling mistakes in on-screen text (from visual analysis).

Return output in strict JSON with fields:
{{
  "mismatches": [
    {{"time": "...", "detail": "..."}}
  ],
  "spelling_errors": [
    {{"time": "...", "word": "..."}}
  ]
}}
"""
    
async def main(video_source: str):
    os.makedirs("reports", exist_ok=True)
    job_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"\n🚀 [BACKEND] Starting new analysis pipeline for job {job_id}.")
    print(f"  [BACKEND] Input video source: {video_source}")

    if video_source.startswith("http") and "drive.google.com" in video_source:
        video_source = convert_drive_link(video_source)
        print(f"  [BACKEND] 🔗 Converted Google Drive link to direct download.")

    print(f"  [BACKEND] ⏳ Starting transcription and visual analysis tasks in parallel...")
    transcript_task = asyncio.create_task(run_transcription(video_source))
    visual_task = asyncio.create_task(run_visual_analysis(video_source))

    transcript = await transcript_task
    print(f"  [BACKEND] ✅ Transcription task complete.")
    
    visual = await visual_task
    print(f"  [BACKEND] ✅ Visual analysis task complete.")

    combined = {
        "job_id": job_id,
        "input": video_source,
        "transcription": transcript,
        "visual_analysis": visual
    }

    combined_path = os.path.join("reports", "combined_output.json")
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
    print(f"  [BACKEND] 📄 Combined intermediate output saved.")

    print(f"  [BACKEND] 🧠 Calling Gemini LLM for comparison...")
    prompt = build_prompt(transcript, visual)
    llm_result = run_llm(prompt)
    print(f"  [BACKEND] ✅ Gemini LLM analysis complete.")

    final_report = {**combined, "comparison": llm_result}
    

    final_path = os.path.join("reports", f"{job_id}_final_report.json")

    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)

    print(f"  [BACKEND] ✨ Final report saved -> {final_path}")
    print(f"  [BACKEND] Pipeline finished successfully for job {job_id}.")

    
    return final_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Usage: python compare.py <video_file_or_url>")
        sys.exit(1)

    video_source = sys.argv[1]
    asyncio.run(main(video_source))