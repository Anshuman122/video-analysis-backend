import os
import json
import asyncio
from datetime import datetime

# FastAPI and SQLAlchemy Imports
from fastapi import FastAPI, Form, Depends, HTTPException, BackgroundTasks, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Import from your local files
from .compare import main as process_video
from .database import SessionLocal, engine, get_db
from . import models
from .auth import verify_token, get_current_user # Make sure to import get_current_user

# This line creates your database tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)

# ======== HELPER FUNCTIONS ========

async def process_video_and_update_db(video_url: str, job_id: int):
    db = SessionLocal()
    job = db.query(models.AnalysisJob).filter(models.AnalysisJob.id == job_id).first()
    if not job:
        print(f"[BACKGROUND] Error: Job {job_id} not found at start of task.")
        db.close()
        return

    try:
        print(f"[BACKGROUND] Starting analysis for job {job_id}.")
        final_report_path = await process_video(video_url, job_id)

        if not final_report_path or not os.path.exists(final_report_path):
            job.status = "failed"
            print(f"[BACKGROUND] Error: Report file not generated for job {job_id}.")
        else:
            with open(final_report_path, "r", encoding="utf-8") as f:
                report = json.load(f)
            
            job.result = json.dumps(report, indent=2)
            job.status = "completed"
            print(f"[BACKGROUND] ✅ Job {job_id} completed successfully.")
        
        db.commit()

    except Exception as e:
        print(f"[BACKGROUND] 💥 CRITICAL ERROR during analysis for job {job_id}: {e}")
        db.rollback() 
        job.status = "failed"
        db.commit()

    finally:
        db.close()

# ======== API ENDPOINTS ========

@app.post("/analyze")
async def analyze(
    background_tasks: BackgroundTasks,
    video_url: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Get the full user object
):
    print("\n[MAIN] Received request on /analyze endpoint.")
    
    # Use the integer ID from the user object to create the job
    new_job = models.AnalysisJob(
        video_url=video_url, 
        status="processing",
        owner_id=current_user.id # <-- THIS IS THE FIX
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    background_tasks.add_task(process_video_and_update_db, video_url, new_job.id)

    print(f"[MAIN] ✅ Job {new_job.id} started in the background.")
    return {"message": "Analysis has started", "job_id": new_job.id}

@app.get("/history")
def get_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Get the full user object
):
    # Use the integer ID from the user object to filter the jobs
    jobs = db.query(models.AnalysisJob).filter(
        models.AnalysisJob.owner_id == current_user.id # <-- THIS IS THE FIX
    ).order_by(models.AnalysisJob.created_at.desc()).all()
    
    for job in jobs:
        if job.result:
            job.result = json.loads(job.result)
    return jobs

@app.get("/download/{job_id}")
def download_report(
    job_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Protect the endpoint
):
    job = db.query(models.AnalysisJob).filter(
        models.AnalysisJob.id == job_id,
        models.AnalysisJob.owner_id == current_user.id # Ensure user owns this job
    ).first()

    if not job or not job.result:
        raise HTTPException(status_code=404, detail="Report not found or not completed.")

    filename = f"{job_id}_report.json"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    
    return Response(content=job.result, media_type="application/json", headers=headers)

@app.get("/status/{job_id}")
def get_job_status(
    job_id: int, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user) # Protect the endpoint
):
    job = db.query(models.AnalysisJob).filter(
        models.AnalysisJob.id == job_id,
        models.AnalysisJob.owner_id == current_user.id # Ensure user owns this job
    ).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status == "completed":
        return {"status": job.status, "result": json.loads(job.result)}
        
    return {"status": job.status}

