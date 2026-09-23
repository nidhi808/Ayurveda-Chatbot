@echo off
echo ===================================================
echo Starting AyurBot FastAPI Backend on port 8000...
echo ===================================================
cd /d "%~dp0"
call venv\Scripts\activate.bat
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
pause
