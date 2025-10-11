import os
import json
import asyncio
import sys
from datetime import datetime
import re

# Your local imports
from .transcription import transcribe_video, convert_drive_link
from .tweleve_labs_visualization import analyze_video

# Third-party imports
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Gemini model setup
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("WARNING: GEMINI_API_KEY not set. LLM features disabled.")

print(f"✅ Using google-generativeai version: {genai.__version__}")

model = None
if API_KEY:
    try:
        model = genai.GenerativeModel("gemini-2.5-flash") # Changed to 1.5-flash for latest features
    except Exception as e:
        print("WARNING: Could not initialize Gemini model:", e)


async def run_transcription(video_source: str):
    """Run transcription by calling the ML Worker API."""
    transcript_file = os.path.join("reports", "transcript.json")
    path = await transcribe_video(video_source, transcript_file)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def repair_and_parse_json(text_to_fix: str) -> dict:
    """Uses Gemini to fix a potentially broken JSON string."""
    if not model:
        return {"scenes": [], "error": "LLM not configured for JSON repair"}
    
    print("  [BACKEND]  🤖  Asking Gemini to repair potentially broken JSON...")
    prompt = f"""The following text is supposed to be a single, valid JSON object but is broken. Please correct any syntax errors and return ONLY the raw, valid JSON object.
BROKEN TEXT:
{text_to_fix}
CORRECTED JSON:
"""
    try:
        response = model.generate_content(prompt)
        repaired_text = response.text.strip()
        if repaired_text.startswith("```"):
            repaired_text = re.search(r'\{.*\}', repaired_text, re.DOTALL).group(0)
        
        print("  [BACKEND]  ✅  JSON repaired. Parsing...")
        return json.loads(repaired_text)
    except Exception as e:
        print(f"  [BACKEND]  ❌  Failed to repair and parse JSON. Error: {e}")
        return {"scenes": [], "error": "Failed to parse visual analysis after repair."}

# ======== CHANGED FUNCTION ========
async def run_visual_analysis(video_source: str):
    """
    Handles the dictionary output from analyze_video and attempts self-healing if needed.
    """
    print("  [BACKEND]  👁️  Starting visual analysis task...")
    # This call receives a dictionary from tweleve_labs_visualization.py
    result_dict = await asyncio.to_thread(analyze_video, video_source)

    # Check if the dictionary from analyze_video contains an error key
    if "error" in result_dict and "raw_output" in result_dict:
        print("  [BACKEND]  ⚠️  Internal parsing failed in visualizer. Attempting self-healing.")
        # If it failed, try to repair the raw_output it provided
        healed_dict = repair_and_parse_json(result_dict["raw_output"])
        return healed_dict.get("scenes", []) # Return the list of scenes
    else:
        # If there was no error, the result is already a valid dictionary
        print("  [BACKEND]  ✅  Visual analysis returned a valid dictionary.")
        return result_dict.get("scenes", []) # Return the list of scenes

def run_llm(prompt: str) -> dict:
    """Calls the Gemini model for the final comparison."""
    if model is None:
        return {"raw_output": "LLM not configured; cannot process."}
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.strip("`").replace("json", "", 1).strip()
        return json.loads(text)
    except Exception:
        return {"raw_output": response.text or "LLM returned nothing"}


def build_prompt(transcription, visual_scenes):
    # This now correctly receives the list of visual scenes
    return f"""
You are analyzing a video.
- Transcription (spoken words): {json.dumps(transcription, indent=2)}
- Visual descriptions: {json.dumps(visual_scenes, indent=2)}

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

async def main(video_source: str, job_id: int):
    os.makedirs("reports", exist_ok=True)
    
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
    
    visual_scenes = await visual_task # This is now a list of scenes
    print(f"  [BACKEND] ✅ Visual analysis task complete.")

    combined = {
        "job_id": job_id,
        "input": video_source,
        "transcription": transcript,
        "visual_analysis": visual_scenes # Storing the list of scenes
    }

    # Saving intermediate output is good for debugging but can be commented out later
    combined_path = os.path.join("reports", f"{job_id}_combined_output.json")
    with open(combined_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)
    print(f"  [BACKEND] 📄 Combined intermediate output saved.")

    print(f"  [BACKEND] 🧠 Calling Gemini LLM for comparison...")
    prompt = build_prompt(transcript, visual_scenes)
    llm_result = run_llm(prompt)
    print(f"  [BACKEND] ✅ Gemini LLM analysis complete.")

    final_report = {**combined, "comparison": llm_result}
    
    final_path = os.path.join("reports", f"{job_id}_final_report.json")
    with open(final_path, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2, ensure_ascii=False)

    print(f"  [BACKEND] ✨ Final report saved -> {final_path}")
    print(f"  [BACKEND] Pipeline finished successfully for job {job_id}.")
    
    return final_path

# ======== CHANGED BLOCK ========
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Usage: python compare.py <video_file_or_url>")
        sys.exit(1)

    video_source = sys.argv[1]
    # Provide a dummy job_id for testing from the command line
    # The 'main' function now requires two arguments.
    asyncio.run(main(video_source, job_id=0))