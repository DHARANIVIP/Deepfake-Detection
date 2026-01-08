import cv2
import numpy as np
from loguru import logger

def analyze_fft_frequency(image_path: str) -> float:
    """
    Performs Fast Fourier Transform (FFT) analysis on the image.
    
    Why: Deepfakes (GANs) often leave high-frequency 'checkerboard' artifacts 
    that are invisible to the eye but obvious in the frequency domain.
    
    Returns:
        float: A score between 0.0 and 100.0
               (Higher score = Higher likelihood of being Artificial/Fake)
    """
    try:
        # 1. Read Image in Grayscale
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            logger.warning(f"FFT failed: Could not read image at {image_path}")
            return 0.0

        # 2. Apply FFT (Fast Fourier Transform)
        f = np.fft.fft2(img)
        fshift = np.fft.fftshift(f)
        
        # 3. Calculate Magnitude Spectrum
        # We use log scale because the range of values is massive
        magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1e-10)

        # 4. Analyze High Frequencies (The "Deepfake Signature")
        rows, cols = img.shape
        crow, ccol = rows // 2, cols // 2
        
        # Mask the center (Low Frequencies represent the general face shape)
        # We want to ignore the face shape and only look at the "Texture/Noise"
        mask_size = 30
        magnitude_spectrum[crow-mask_size:crow+mask_size, ccol-mask_size:ccol+mask_size] = 0

        # 5. Calculate Average Noise in High Frequency areas
        mean_magnitude = np.mean(magnitude_spectrum)

        # 6. Normalize Score
        # Real cameras usually have a noise floor around 80-100 in this spectrum.
        # GANs/Deepfakes often spike above 130-150 due to upsampling artifacts.
        
        # Mapping: 100 -> 0% Fake, 160 -> 100% Fake
        normalized_score = (mean_magnitude - 100) * 1.6
        
        # Clamp value between 0 and 100
        final_score = max(0.0, min(normalized_score, 100.0))

        return round(final_score, 2)

    except Exception as e:
        logger.error(f"Error in FFT analysis for {image_path}: {e}")
        return 0.0

# --- Quick Test Block (Runs only if you execute this file directly) ---
if __name__ == "__main__":
    # Create a dummy image to test
    dummy_img = np.zeros((224, 224), dtype=np.uint8)
    cv2.imwrite("test_fft.jpg", dummy_img)
    
    score = analyze_fft_frequency("test_fft.jpg")
    print(f"Test Score: {score}")
    
    # Cleanup
    import os
    os.remove("test_fft.jpg")