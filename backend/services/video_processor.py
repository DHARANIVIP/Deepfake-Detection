import cv2
import os
import time
from loguru import logger
from backend.core.database import db
from backend.services.face_detector import crop_face_from_frame
from backend.services.ai_detector import get_ai_prediction
from backend.services.math_detector import get_fft_score

async def process_video_pipeline(scan_id: str, video_path: str):
    logger.info(f"[{scan_id}] Starting Analysis Pipeline...")
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Strategy: Analyze 1 frame per second to save CPU
    frame_interval = int(fps) 
    
    frame_data = []
    ai_scores = []
    fft_scores = []
    
    count = 0
    analyzed_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        if count % frame_interval == 0:
            timestamp = count / fps
            
            # 1. Detect & Crop Face
            # We don't save to disk to speed up Render. We pass the numpy array directly if possible,
            # but our detectors expect paths. Let's save temp frame.
            temp_frame_path = f"/tmp/{scan_id}_{count}.jpg"
            cv2.imwrite(temp_frame_path, frame)
            
            face_path = crop_face_from_frame(temp_frame_path, "/tmp")
            
            # Default scores
            ai_score = 0.0
            fft_score = 0.0
            
            if face_path:
                # 2. Run AI (HuggingFace / Local)
                ai_score = get_ai_prediction(face_path)
                
                # 3. Run Math (FFT)
                fft_score = get_fft_score(face_path)
                
                # Cleanup temp face
                if os.path.exists(face_path): os.remove(face_path)

            frame_data.append({
                "timestamp": round(timestamp, 2),
                "ai_probability": round(ai_score, 4),
                "fft_anomaly": round(fft_score, 2)
            })
            
            ai_scores.append(ai_score)
            fft_scores.append(fft_score)
            analyzed_count += 1
            
            # Cleanup temp frame
            if os.path.exists(temp_frame_path): os.remove(temp_frame_path)

        count += 1

    cap.release()

    # --- Calculate Final Verdict ---
    if not ai_scores:
        avg_ai = 0
    else:
        avg_ai = sum(ai_scores) / len(ai_scores)
        
    verdict = "DEEPFAKE" if avg_ai > 0.55 else "REAL"
    
    final_report = {
        "scan_id": scan_id,
        "status": "COMPLETED",
        "verdict": verdict,
        "confidence_score": round(avg_ai * 100, 2),
        "total_frames_analyzed": analyzed_count,
        "frame_data": frame_data,
        "created_at": time.time()
    }

    # Save to MongoDB
    if db.db is not None:
        await db.db.scans.insert_one(final_report)
        logger.success(f"[{scan_id}] Analysis Saved to DB. Verdict: {verdict}")
    else:
        logger.error("DB Not connected. Result lost.")