from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from loguru import logger
import shutil
import uuid
import os
import sys

# Ensure we can import from 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import settings
from backend.services.video_processor import process_video_pipeline
from backend.core.database import db

app = FastAPI(title="Nexora Deepfake Defense API", version="2.0")

# --- CORS Configuration ---
# Allow Vercel frontend and Localhost
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://deepfake-detection-omega.vercel.app", # Replace with your actual Vercel URL
    "*" # Keep * for development, restrict in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Events ---
@app.on_event("startup")
async def startup_event():
    logger.info("Nexora API Starting up...")
    db.connect()

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Nexora API Shutting down...")
    db.close()

# --- Static Files Setup ---
# 1. Mount Uploads (Critical for video playback)
# Ensure upload folder exists
os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_FOLDER), name="uploads")

# 2. Mount Frontend (Optional - for Monolithic deployment on Render)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST_DIR = os.path.join(BASE_DIR, "dist")
ASSETS_DIR = os.path.join(DIST_DIR, "assets")

if os.path.exists(ASSETS_DIR):
    app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
else:
    logger.warning(f"Frontend assets not found at {ASSETS_DIR}. Running in API-only mode.")

# --- API Routes ---

@app.post("/api/analyze")
async def analyze_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # 1. Validation
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower() if filename else ""
    
    # Simple extension check
    allowed_exts = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    if ext not in allowed_exts:
        raise HTTPException(status_code=400, detail="Invalid video format. Use MP4, AVI, MOV.")
    
    # 2. Save File
    scan_id = uuid.uuid4().hex
    safe_filename = f"{scan_id}{ext}"
    file_path = os.path.join(settings.UPLOAD_FOLDER, safe_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"File Save Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save video file.")
        
    # 3. Trigger Background Processing
    # Note: We pass the string path to avoid serialization issues
    background_tasks.add_task(process_video_pipeline, scan_id, str(file_path))
    
    return {
        "scan_id": scan_id,
        "message": "Upload successful. Analysis running in background.",
        "status_url": f"/api/results/{scan_id}",
        "video_url": f"/uploads/{safe_filename}" # Useful for frontend to play it
    }

@app.get("/api/results/{scan_id}")
async def get_results(scan_id: str):
    # 1. Check Database
    if db.db is not None:
        try:
            # Check 'scans' collection
            report = await db.db.scans.find_one({"scan_id": scan_id}, {"_id": 0})
            if report:
                return report
        except Exception as e:
            logger.error(f"DB Read Error: {e}")
            # Don't crash, just fall through to processing message
            
    # 2. Fallback Response
    return {"status": "PROCESSING", "message": "Analysis in progress...", "scan_id": scan_id}

@app.get("/api/scans")
async def get_recent_scans():
    if db.db is None:
        logger.warning("Database not connected")
        return []
    
    try:
        # Sort by created_at desc
        cursor = db.db.scans.find({}, {"_id": 0}).sort("created_at", -1).limit(20)
        scans = await cursor.to_list(length=20)
        return scans
    except Exception as e:
        logger.error(f"DB Read Error (Scans): {e}")
        return []

@app.delete("/api/scans/{scan_id}")
async def delete_scan(scan_id: str):
    if db.db is None:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        result = await db.db.scans.delete_one({"scan_id": scan_id})
        
        # Optional: Delete the actual video file too to save space
        # file_path = os.path.join(settings.UPLOAD_FOLDER, f"{scan_id}.mp4")
        # if os.path.exists(file_path): os.remove(file_path)

        if result.deleted_count == 1:
            return {"status": "deleted", "scan_id": scan_id}
        
        raise HTTPException(status_code=404, detail="Scan not found")
    except Exception as e:
        logger.error(f"DB Delete Error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete scan")

# --- SPA Catch-All (For Render/Monolithic Deploys) ---
# This must be at the END so it doesn't block API routes

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    # If API route wasn't matched above, and it starts with 'api', return 404
    if full_path.startswith("api"):
        raise HTTPException(status_code=404, detail="API Endpoint not found")

    # Serve Static Files
    file_path = os.path.join(DIST_DIR, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # Serve Index.html for React Routes
    index_path = os.path.join(DIST_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {"status": "Backend API Running", "info": "Frontend not found. Use /api/ endpoints."}