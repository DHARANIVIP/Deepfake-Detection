import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env only if running locally
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = "Nexora Deepfake Defense"
    VERSION: str = "2.5.0"
    
    # Paths
    STORAGE_DIR = BASE_DIR / "storage"
    UPLOAD_FOLDER = STORAGE_DIR / "uploads"
    PROCESSED_FOLDER = STORAGE_DIR / "processed"
    
    # Secrets (Read from Render Env Vars)
    MONGO_URI: str = os.getenv("MONGO_URI")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "sentinel_ai")
    HF_TOKEN: str = os.getenv("HF_TOKEN")
    
    # Deployment: The URL of your Vercel Frontend
    # Example: https://nexora-frontend.vercel.app
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173") 
    
    ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

settings = Settings()

# Ensure folders exist
for folder in [settings.UPLOAD_FOLDER, settings.PROCESSED_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)