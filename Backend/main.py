from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import asyncio
from compare import main as process_video

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

HISTORY_FILE = "reports/history.json"


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


@app.post("/analyze")
async def analyze(video_url: str = Form(...)):

    print("\n[MAIN] Received request on /analyze endpoint.")
    print("[MAIN] ⏳ Calling video processing pipeline...")
    

    final_report_path = await process_video(video_url)
    

    print("[MAIN] ✅ Video processing pipeline finished.")

    if not final_report_path or not os.path.exists(final_report_path):
        print("[MAIN] ❌ Error: Final report file was not found.")
        return {"error": "Report generation failed"}

    print(f"[MAIN] 📄 Loading final report from {final_report_path}.")
    with open(final_report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    print("[MAIN] 💾 Saving new report to history file...")
    history = load_history()
    history.append(report)
    save_history(history)
    print("[MAIN] ✅ Report saved to history.")

    print("[MAIN] ✨ Returning final report to frontend.")
    return report


@app.get("/history")
async def get_history():

    print("\n[MAIN] Received request on /history endpoint. Loading history...")
    return load_history()


@app.get("/download/{job_id}")
async def download_report(job_id: str):

    print(f"\n[MAIN] Received request on /download for job_id: {job_id}")
    path = os.path.join("reports", f"{job_id}_final_report.json")
    if not os.path.exists(path):
    
        print(f"[MAIN] ❌ Report for job_id {job_id} not found.")
        return {"error": "Report not found"}
    
    print(f"[MAIN] ✅ Report found. Sending file content.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
