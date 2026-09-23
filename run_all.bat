@echo off
echo ===================================================
echo Starting AyurBot System (Backend + Frontend)...
echo ===================================================
cd /d "%~dp0"
start "AyurBot Backend" cmd /c "run_backend.bat"
timeout /t 3 /nobreak >nul
start "AyurBot Frontend" cmd /c "run_frontend.bat"
echo AyurBot services initiated!
echo Backend:  http://localhost:8000/docs
echo Frontend: http://localhost:5173
