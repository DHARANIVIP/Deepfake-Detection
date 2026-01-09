from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from loguru import logger
import shutil
import uuid
import os
import json

from backend.core.config import settings
from backend.services.video_processor import process_video_pipeline

app = FastAPI(title="Nexora Deepfake Defense API", version="2.0")

# CORS (Allow Frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.core.database import db

@app.on_event("startup")
async def startup_event():
    logger.info("Nexora API Starting up...")
    db.connect()

@app.on_event("shutdown")
async def shutdown_event():
    db.close()

# --- serve static files ---
dist_dir = "dist"
assets_dir = os.path.join(dist_dir, "assets")

# Mount the assets folder (JS/CSS) ONLY if it exists (Render deployment might only have backend)
if os.path.exists(assets_dir) and os.path.isdir(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
else:
    logger.warning(f"Assets directory '{assets_dir}' not found. Frontend will not be served from here.")

# Mount uploads for video playback (Frontend needs to access http://localhost:8000/uploads/video.mp4)
if not os.path.exists(settings.UPLOAD_FOLDER):
    os.makedirs(settings.UPLOAD_FOLDER)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_FOLDER), name="uploads")

# API Routes

@app.post("/api/analyze")
async def analyze_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # 1. Validation
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid video format")
    
    # 2. Save File
    scan_id = uuid.uuid4().hex
    file_path = settings.UPLOAD_FOLDER / f"{scan_id}{ext}"
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 3. Trigger Background Processing
    background_tasks.add_task(process_video_pipeline, scan_id, str(file_path))
    
    return {
        "scan_id": scan_id,
        "message": "Upload successful. Analysis running in background.",
        "status_url": f"/api/results/{scan_id}"
    }

@app.get("/api/results/{scan_id}")
async def get_results(scan_id: str):
    # 1. Try DB (Sole Source of Truth)
    if db.db is not None:
        try:
            report = await db.db.scans.find_one({"scan_id": scan_id}, {"_id": 0})
            if report:
                return report
        except Exception as e:
            logger.error(f"DB Read Error: {e}")
            raise HTTPException(status_code=500, detail="Database Error")

    # If we are here, it's either not connected or not found
    return {"status": "PROCESSING", "message": "Analysis in progress or ID not found..."}

# --- SPA Catch-All ---

@app.get("/")
async def serve_index():
    index_path = os.path.join(dist_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"status": "Backend Running", "info": "Frontend files not found (deployed separately)."}

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # Security: prevent traversing up
    if ".." in full_path:
        raise HTTPException(status_code=404)
        
    file_path = os.path.join(dist_dir, full_path)
    
    # If it is a file, serve it directly
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Otherwise, check for index.html for client-side routing
    index_path = os.path.join(dist_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
        
    # If no frontend files, just return 404 for non-api routes
    raise HTTPException(status_code=404, detail="File not found")