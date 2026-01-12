from fastapi import FastAPI, File, UploadFile, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import shutil
import uuid
import os
from loguru import logger

from backend.core.config import settings
from backend.core.database import db
from backend.services.video_processor import process_video_pipeline

app = FastAPI(title="Nexora API", version=settings.VERSION)

# --- CORS (Crucial for Vercel) ---
origins = [
    "http://localhost:5173", # Local dev
    settings.FRONTEND_URL,   # Your Vercel URL
    "*"                      # Allow all (Emergency fallback)
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
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.close()

# --- Static Files (Video Playback) ---
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_FOLDER), name="uploads")

# --- Routes ---
@app.post("/api/analyze")
async def analyze_video(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    # Validate extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid video format")

    # Generate ID and Path
    scan_id = uuid.uuid4().hex
    filename = f"{scan_id}{ext}"
    file_path = settings.UPLOAD_FOLDER / filename

    # Save File
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Server write error")

    # Start Background Analysis
    background_tasks.add_task(process_video_pipeline, scan_id, str(file_path))

    return {
        "scan_id": scan_id,
        "message": "Processing started",
        "video_url": f"/uploads/{filename}" # Frontend uses this to play video
    }

@app.get("/api/results/{scan_id}")
async def get_results(scan_id: str):
    if db.db is None:
        return {"status": "PROCESSING", "message": "DB not connected"}
        
    try:
        report = await db.db.scans.find_one({"scan_id": scan_id}, {"_id": 0})
        if report:
            return report
        else:
            return {"status": "PROCESSING", "message": "Analysis in progress..."}
    except Exception as e:
        logger.error(f"DB Read Error: {e}")
        return {"status": "ERROR", "message": "Database error"}

@app.get("/api/scans")
async def get_history():
    if db.db is None: return []
    try:
        cursor = db.db.scans.find({}, {"_id": 0}).sort("created_at", -1).limit(20)
        return await cursor.to_list(length=20)
    except:
        return []

@app.get("/")
def health_check():
    return {"status": "online", "service": "Nexora Backend"}