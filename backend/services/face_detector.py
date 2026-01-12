import logging
import os
from loguru import logger

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

# MediaPipe is optional (Too heavy for free tier)
try:
    import mediapipe as mp
    mp_face_detection = mp.solutions.face_detection
    detector = mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.6)
except ImportError:
    detector = None
    # Pre-load Haar Cascade as fallback
    face_cascade = None
    if cv2:
        # Try finding the XML in standard paths
        xml_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(xml_path)

def crop_face_advanced(frame):
    """
    Detects face using MediaPipe (Best) -> Haar Cascade (Fast) -> Center Crop (Fallback).
    Returns: (cropped_face_numpy, found_boolean)
    """
    if cv2 is None:
        return None, False # Cannot process without CV2

    height, width, _ = frame.shape

    # 1. Try MediaPipe (If installed)
    if detector:
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = detector.process(rgb_frame)
            if results.detections:
                detection = results.detections[0]
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * width)
                y = int(bbox.ymin * height)
                w = int(bbox.width * width)
                h = int(bbox.height * height)
                
                # Padding
                x_pad, y_pad = int(w * 0.2), int(h * 0.2)
                x1, y1 = max(0, x - x_pad), max(0, y - y_pad)
                x2, y2 = min(width, x + w + x_pad), min(height, y + h + y_pad)
                
                return frame[y1:y2, x1:x2], True
        except Exception as e:
            logger.warning(f"MediaPipe Failed: {e}")

    # 2. Try Haar Cascade (Lightweight Fallback)
    if face_cascade:
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            if len(faces) > 0:
                x, y, w, h = faces[0]
                # Padding
                pad = int(w * 0.2)
                x1, y1 = max(0, x - pad), max(0, y - pad)
                x2, y2 = min(width, x + w + pad), min(height, y + h + pad)
                return frame[y1:y2, x1:x2], True
        except Exception as e:
            logger.warning(f"Haar Cascade Failed: {e}")

    # 3. Last Resort: Center Crop (Better than crashing)
    # If no face detected, assume center of video is relevant
    h_center, w_center = height // 2, width // 2
    h_size, w_size = height // 2, width // 2 # 50% crop
    y1 = max(0, h_center - h_size // 2)
    x1 = max(0, w_center - w_size // 2)
    return frame[y1:y1+h_size, x1:x1+w_size], True