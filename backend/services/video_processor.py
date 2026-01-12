import os
import json
import time
import random
from loguru import logger
from backend.core.config import settings
from backend.core.database import db

# Optional Imports with Graceful Fallback
try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None
    logger.warning("OpenCV/Numpy not found. Running in LITE MODE (Mock Processing).")

# Import services (which now also handle missing deps)
from backend.services.face_detector import crop_face_advanced
from backend.services.ai_detector import get_ai_prediction, get_fft_score

async def process_video_pipeline(scan_id: str, video_path: str):
    logger.info(f"[{scan_id}] Processing Started: {video_path}")
    
    # 1. Setup
    frame_save_dir = settings.PROCESSED_FOLDER / scan_id
    frame_save_dir.mkdir(exist_ok=True)
    
    analyzed_frames = []
    fake_accumulated_score = 0
    fft_accumulated_score = 0
    count = 0
    
    # --- MOCK MODE (If OpenCV is missing) ---
    if cv2 is None:
        logger.info(f"[{scan_id}] CV2 missing. Simulating analysis...")
        time.sleep(3) 
        
        # Generator fake frame data
        for i in range(5):
            ai_conf = random.uniform(0.1, 0.95)
            fft_val = random.uniform(10, 80)
            analyzed_frames.append({
                "timestamp": i * 1.0,
                "ai_probability": ai_conf,
                "fft_anomaly": fft_val
            })
            fake_accumulated_score += ai_conf
            fft_accumulated_score += fft_val
            count += 1
            
    # --- REAL MODE ---
    else:
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                logger.error(f"Could not open video: {video_path}")
                return

            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            skip_rate = int(fps) * 2 # Process every 2 seconds for performance 
            current_frame = 0
            
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                
                if current_frame % skip_rate == 0:
                    # A. Detect Face
                    face_img, found = crop_face_advanced(frame)
                    
                    if found:
                        face_filename = f"face_{current_frame}.jpg"
                        face_path = frame_save_dir / face_filename
                        cv2.imwrite(str(face_path), face_img)
                        
                        # B. Run Intelligence
                        ai_conf = get_ai_prediction(str(face_path))
                        fft_val = get_fft_score(str(face_path))
                        
                        analyzed_frames.append({
                            "timestamp": round(current_frame / fps, 2),
                            "ai_probability": ai_conf,
                            "fft_anomaly": fft_val
                        })
                        
                        fake_accumulated_score += ai_conf
                        fft_accumulated_score += fft_val
                        count += 1
                        
                current_frame += 1

            cap.release()
        except Exception as e:
            logger.error(f"Error in video processing loop: {e}")

    # 2. Final Verdict Logic
    if count == 0:
        final_verdict = "UNCERTAIN"
        confidence = 0
    else:
        avg_ai = fake_accumulated_score / count
        avg_fft = fft_accumulated_score / count
        
        # Weighted Logic: AI is 70% important, Math is 30%
        final_score = (avg_ai * 100 * 0.7) + (avg_fft * 0.01 * 100 * 0.3)
        confidence = min(final_score, 99.9)
        final_verdict = "DEEPFAKE" if confidence > 50 else "REAL"

    # 3. Save Report
    report = {
        "scan_id": scan_id,
        "verdict": final_verdict,
        "confidence_score": round(confidence, 2),
        "total_frames_analyzed": count,
        "frame_data": analyzed_frames,
        "created_at": time.time()
    }
    
    # Save to MongoDB (Async)
    try:
        if db.db is not None:
            await db.db.scans.insert_one(report)
            logger.success(f"[{scan_id}] Saved to MongoDB Atlas")
        else:
            logger.warning("MongoDB not connected. Data NOT saved.")
    except Exception as e:
        logger.error(f"DB Save Failed: {e}")

    # 4. Cleanup Temporary Files (Cloud Mode)
    try:
        import shutil
        # Delete extracted frames folder
        if frame_save_dir.exists():
            shutil.rmtree(frame_save_dir)
        
        # Delete uploaded video file
        # if os.path.exists(video_path):
        #    os.remove(video_path)
            
        logger.info(f"[{scan_id}] Cleanup successful (Frames cleared, Video kept for playback)")
    except Exception as e:
        logger.error(f"Cleanup Failed: {e}")

    logger.success(f"[{scan_id}] Analysis Complete. Verdict: {final_verdict}")