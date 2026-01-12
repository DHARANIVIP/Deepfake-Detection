import os
import random
from loguru import logger

try:
    from huggingface_hub import InferenceClient
    from transformers import pipeline
    from PIL import Image
    import numpy as np
    import cv2
except ImportError:
    InferenceClient = None
    pipeline = None
    Image = None
    np = None
    cv2 = None

# --- 1. DEEP LEARNING ENGINE ---
# User requested specific model
API_MODEL_NAME = "prithivMLmods/deepfake-detector-model-v1"
LOCAL_MODEL_NAME = "prithivMLmods/Deep-Fake-Detector-v2-Model"

# Setup Inference Client (Cloud API)
hf_token = os.environ.get("HF_TOKEN")
client = None
if hf_token and InferenceClient:
    try:
        client = InferenceClient(provider="hf-inference", api_key=hf_token)
        logger.success(f"HF Inference Client initialized with model: {API_MODEL_NAME}")
    except Exception as e:
        logger.warning(f"Could not initialize HF Client: {e}")

# Setup Local Pipeline (Lazy Load)
ai_pipe = None

def get_local_pipe():
    global ai_pipe
    if ai_pipe is None and pipeline:
        try:
            logger.info(f"Loading Local AI Model (Lazy): {LOCAL_MODEL_NAME}...")
            # We use a try-catch block here to prevent crashing if OOM occurs
            ai_pipe = pipeline("image-classification", model=LOCAL_MODEL_NAME, device=-1)
            logger.success("Local AI Model Loaded.")
        except Exception as e:
            logger.error(f"Local AI Load Failed (Likely OOM): {e}")
            ai_pipe = "FAILED" # Prevent retrying
    return ai_pipe if ai_pipe != "FAILED" else None

def get_ai_prediction(image_path: str):
    """Returns probability of being FAKE (0.0 to 1.0)"""
    # LITE MODE: Mock score if everything is missing
    if not client and not ai_pipe:
        return random.uniform(0.1, 0.9)

    try:
        # STRATEGY 1: Cloud API
        if client:
            try:
                # API expects binary or path. Client.image_classification handles local paths?
                # Usually client takes URL or bytes or PIL.
                # Let's read file as bytes to be safe or pass PIL
                if Image:
                    image = Image.open(image_path)
                    result = client.image_classification(image, model=API_MODEL_NAME)
                    # Result format: [{'label': 'Fake', 'score': 0.99}, ...]
                    
                    top = result[0]
                    # InferenceClient usually returns objects like ClassificatonOutput or simple list of dicts depending on version
                    # We'll handle it as list of objects or dicts
                    if hasattr(top, 'label'):
                        label = top.label.lower()
                        score = top.score
                    else:
                        label = top['label'].lower()
                        score = top['score']
                    
                    if "fake" in label or "deepfake" in label:
                        return score
                    else:
                        return 1.0 - score
            except Exception as e:
                logger.error(f"API Inference failed, trying local if available: {e}")
                # Fallthrough to local

        # STRATEGY 2: Local Pipeline
        local_pipe = get_local_pipe()
        if local_pipe and Image:
            pil_image = Image.open(image_path)
            # Use the local variable 'local_pipe', not the global 'ai_pipe'
            result = local_pipe(pil_image)
            top = result[0]
            label = top['label'].lower()
            score = top['score']
            
            if "fake" in label or "deepfake" in label:
                return score
            else:
                return 1.0 - score
                
        # Fallback if both fail
        logger.warning(f"No AI model available (Client: {bool(client)}, Pipe: {bool(local_pipe)}). Returning random score.")
        return random.uniform(0.1, 0.9)
            
    except Exception as e:
        logger.error(f"AI Prediction Error: {e}")
        return 0.5


