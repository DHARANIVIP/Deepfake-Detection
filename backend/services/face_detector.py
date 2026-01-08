import logging
try:
    import cv2
    import mediapipe as mp
    import numpy as np
    
    # Initialize MediaPipe Face Detection
    mp_face_detection = mp.solutions.face_detection
    detector = mp_face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.6)
except ImportError:
    cv2 = None
    mp = None
    np = None
    detector = None

from loguru import logger

def crop_face_advanced(frame):
    """
    Detects face using Google MediaPipe and returns the cropped numpy array.
    Returns: (cropped_face, status_boolean)
    """
    if detector is None:
        # Lite Mode: Simulate finding a face (return None or random noise if needed, or just True)
        return None, True 

    try:
        height, width, _ = frame.shape
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = detector.process(rgb_frame)

        if not results.detections:
            return None, False

        # Get the first face (Assumption: Single person video)
        detection = results.detections[0]
        bbox = detection.location_data.relative_bounding_box

        # Convert relative coordinates to pixels
        x = int(bbox.xmin * width)
        y = int(bbox.ymin * height)
        w = int(bbox.width * width)
        h = int(bbox.height * height)

        # Add Padding (20%) to capture chin/forehead artifacts
        x_pad, y_pad = int(w * 0.2), int(h * 0.2)
        x1 = max(0, x - x_pad)
        y1 = max(0, y - y_pad)
        x2 = min(width, x + w + x_pad)
        y2 = min(height, y + h + y_pad)

        cropped_face = frame[y1:y2, x1:x2]
        return cropped_face, True

    except Exception as e:
        logger.error(f"Face Detection Failed: {e}")
        return None, False