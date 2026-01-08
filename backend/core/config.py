import os
from pathlib import Path

class Settings:
    PROJECT_NAME: str = "Deepfake Defense System"
    VERSION: str = "2.0 (Advanced)"
    
    # Dynamic Path Setup
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    STORAGE_DIR = BASE_DIR / "storage"
    
    UPLOAD_FOLDER = STORAGE_DIR / "uploads"
    PROCESSED_FOLDER = STORAGE_DIR / "processed"
    RESULTS_FOLDER = STORAGE_DIR / "results"
    
    # Allowed Video Formats
    # Allowed Video Formats
    ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}

    # Database
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb+srv://vvdharani57_db_user:GPRXbgUnuzy9FSnW@cluster0.tnkfodr.mongodb.net/?appName=Cluster0")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "sentinel_ai")

settings = Settings()

# Auto-create directories on start
for folder in [settings.UPLOAD_FOLDER, settings.PROCESSED_FOLDER, settings.RESULTS_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)