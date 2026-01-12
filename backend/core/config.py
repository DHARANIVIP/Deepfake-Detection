import os
from pathlib import Path
from dotenv import load_dotenv # Make sure to pip install python-dotenv

# 1. Setup Base Directory
# Refers to: backend/
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. Load .env file (Secrets)
# Looks for backend/.env
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    PROJECT_NAME: str = "Deepfake Defense System"
    VERSION: str = "2.0 (Advanced)"
    
    # 3. Dynamic Path Setup
    # All storage will be inside backend/storage/
    STORAGE_DIR = BASE_DIR / "storage"
    
    UPLOAD_FOLDER = STORAGE_DIR / "uploads"
    PROCESSED_FOLDER = STORAGE_DIR / "processed"
    RESULTS_FOLDER = STORAGE_DIR / "results"
    
    # 4. Allowed Video Formats
    ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

    # 5. Database (SECURE WAY)
    # Reads from .env file, fallback is None to raise error if missing
    MONGO_URI: str = os.getenv("MONGO_URI")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "sentinel_ai")

settings = Settings()

# 6. Auto-create directories on start
# This ensures we don't get "File Not Found" errors
for folder in [settings.UPLOAD_FOLDER, settings.PROCESSED_FOLDER, settings.RESULTS_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)