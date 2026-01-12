import cv2
import numpy as np
from loguru import logger

def get_fft_score(image_path: str) -> float:
    """
    Returns a score 0-100.
    Higher score means more 'checkerboard' artifacts (common in Deepfakes).
    """
    try:
        img = cv2.imread(image_path, 0) # Grayscale
        if img is None: return 0.0

        # FFT Transform
        f = np.fft.fft2(img)
        fshift = np.fft.fftshift(f)
        magnitude = 20 * np.log(np.abs(fshift) + 1e-10)

        # Analyze High Frequencies (Edges)
        rows, cols = img.shape
        crow, ccol = rows//2, cols//2
        mask_size = 30
        
        # Block low frequencies (center)
        magnitude[crow-mask_size:crow+mask_size, ccol-mask_size:ccol+mask_size] = 0
        
        score = np.mean(magnitude)
        
        # Normalize (Heuristic)
        # Real images usually < 110. Fakes > 130.
        normalized = min(max((score - 100) * 2, 0), 100)
        
        return float(normalized)

    except Exception as e:
        logger.warning(f"FFT Error: {e}")
        return 0.0