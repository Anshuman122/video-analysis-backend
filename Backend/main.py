from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import asyncio
from Backend.compare import main as process_video

app = FastAPI()

# Allow frontend (React) to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later replace with http://localhost:5173 or http://localhost:3000
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
    """Trigger video analysis pipeline"""
    await process_video(video_url)

    final_report_path = os.path.join("reports", "final_report.json")
    if not os.path.exists(final_report_path):
        return {"error": "Report generation failed"}

    with open(final_report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    # Save history
    history = load_history()
    history.append(report)
    save_history(history)

    return report


@app.get("/history")
async def get_history():
    """Return all previous reports"""
    return load_history()


@app.get("/download/{job_id}")
async def download_report(job_id: str):
    """Download specific report"""
    path = os.path.join("reports", f"{job_id}_final_report.json")
    if not os.path.exists(path):
        return {"error": "Report not found"}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
