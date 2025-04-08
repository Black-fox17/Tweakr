from fastapi import FastAPI, BackgroundTasks, Query, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import os
import time
import uuid
from datetime import datetime

from datapipeline.core.constants import MONGODB_ATLAS_CLUSTER_URI, MONGO_DB_NAME
from datapipeline.main import PapersPipeline
from datapipeline.models.papers import Papers
app = APIRouter()


class ProcessPapersRequest(BaseModel):
    query: str
    category: str
    batch_size: int = 20
    download_dir: str = "./store"
    sources: List[str] = ["arxiv", "elsevier", "springer", "pubmed", "ieee", "acm"]

class ProcessPapersResponse(BaseModel):
    status: str
    message: str
    job_id: str

class LogEntry(BaseModel):
    timestamp: str
    message: str
    type: str  # 'error' | 'processing' | 'existing' | 'success' | 'info'

class JobStats(BaseModel):
    papersProcessed: int
    totalSources: int
    progress: float
    batchSize: int
    elapsedTime: int
    isProcessing: bool

# Track background tasks
active_jobs = {}

# Store logs for each job
job_logs = {}

# Track statistics for each job
job_stats = {}

def add_log(job_id: str, message: str, log_type: str):
    """Add a log entry for a job"""
    if job_id not in job_logs:
        job_logs[job_id] = []
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    job_logs[job_id].append({
        "timestamp": timestamp,
        "message": message,
        "type": log_type
    })

def update_stats(job_id: str, **kwargs):
    """Update stats for a job"""
    if job_id not in job_stats:
        job_stats[job_id] = {
            "papersProcessed": 0,
            "totalSources": 0,
            "progress": 0,
            "batchSize": 20,
            "elapsedTime": 0,
            "isProcessing": False
        }
    
    for key, value in kwargs.items():
        if key in job_stats[job_id]:
            job_stats[job_id][key] = value

def process_papers_task(
    job_id: str, 
    query: str, 
    category: str, 
    batch_size: int, 
    download_dir: str, 
    sources: List[str]
):
    """Background task to process papers."""
    try:
        # Ensure download directory exists
        os.makedirs(download_dir, exist_ok=True)
        
        # Initialize stats
        start_time = time.time()
        update_stats(
            job_id,
            papersProcessed=0,
            totalSources=len(sources),
            progress=0,
            batchSize=batch_size,
            elapsedTime=0,
            isProcessing=True
        )
        
        # Update elapsed time in a separate thread
        def update_elapsed_time():
            while job_stats[job_id]["isProcessing"]:
                elapsed = int(time.time() - start_time)
                update_stats(job_id, elapsedTime=elapsed)
                time.sleep(1)
        
        import threading
        timer_thread = threading.Thread(target=update_elapsed_time)
        timer_thread.daemon = True
        timer_thread.start()
        
        # Initialize the pipeline with logging
        pipeline = PapersPipeline(
            mongo_uri=MONGODB_ATLAS_CLUSTER_URI,
            mongo_db_name=MONGO_DB_NAME,
            job_id=job_id
        )
        
        # Process papers
        pipeline.process_papers(
            query=query,
            category=category,
            batch_size=batch_size,
            download_dir=download_dir,
            sources=sources
        )
        
        # Update job status
        active_jobs[job_id] = {"status": "completed", "message": "Papers processing completed successfully"}
    
    except Exception as e:
        # Update job status with error
        active_jobs[job_id] = {"status": "failed", "message": f"Error processing papers: {str(e)}"}
        add_log(job_id, f"Job failed: {str(e)}", "error")
        update_stats(job_id, isProcessing=False)

@app.post("/api/papers/process", response_model=ProcessPapersResponse)
async def process_papers(
    background_tasks: BackgroundTasks,
    request: ProcessPapersRequest
):
    """
    Endpoint to process academic papers from various sources.
    
    This will search and download papers matching the query from the specified sources,
    extract their content, generate keywords, and store them in both MongoDB and SQL database.
    """
    # Generate a unique job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    active_jobs[job_id] = {"status": "started", "message": "Paper processing job started"}
    job_logs[job_id] = []
    
    # Add the task to background tasks
    background_tasks.add_task(
        process_papers_task,
        job_id=job_id,
        query=request.query,
        category=request.category,
        batch_size=request.batch_size,
        download_dir=request.download_dir,
        sources=request.sources
    )
    
    return {
        "status": "started",
        "message": "Paper processing job started in the background",
        "job_id": job_id
    }

@app.get("/api/papers/jobs/{job_id}", response_model=ProcessPapersResponse)
async def get_job_status(job_id: str):
    """
    Endpoint to check the status of a paper processing job.
    """
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_info = active_jobs[job_id]
    return {
        "status": job_info["status"],
        "message": job_info["message"],
        "job_id": job_id
    }

@app.get("/api/papers/jobs/{job_id}/logs")
async def get_job_logs(job_id: str):
    """
    Endpoint to get logs for a specific job.
    """
    if job_id not in job_logs:
        raise HTTPException(status_code=404, detail="Job logs not found")
    
    return job_logs[job_id]

@app.get("/api/papers/jobs/{job_id}/stats")
async def get_job_stats(job_id: str):
    """
    Endpoint to get stats for a specific job.
    """
    if job_id not in job_stats:
        raise HTTPException(status_code=404, detail="Job stats not found")
    
    return job_stats[job_id]

@app.get("/api/papers/sources", response_model=List[str])
async def get_available_sources():
    """
    Endpoint to get the list of available paper sources.
    """
    return ["arxiv", "elsevier", "springer", "pubmed", "ieee", "acm"]