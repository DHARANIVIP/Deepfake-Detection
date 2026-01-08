@echo off
echo Starting Sentinel AI System (Single Server Mode)...

:: Start Backend (which now serves Frontend too)
echo Access the App at: http://localhost:8000
echo.
cmd /k "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

pause
