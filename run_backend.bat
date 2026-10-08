@echo off
echo ===================================================
echo Starting AyurBot FastAPI Backend on port 8000...
echo ===================================================
cd /d "%~dp0"
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    echo [Notice] Local venv not found. Attempting to run with system python...
    python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
)
pause
