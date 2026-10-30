@echo off
title CitizenShield Municipal Production Server
echo ========================================================
echo   Starting CitizenShield Municipal Backend (Waitress WSGI)...
echo   Running on: http://127.0.0.1:5000 / http://localhost:5000
echo ========================================================
echo.
cd /d "%~dp0"
python run.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Server terminated with error code %ERRORLEVEL%.
    pause
)
