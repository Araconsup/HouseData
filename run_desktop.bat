@echo off
title HOUSEDATA - Tehran Real Estate Platform
echo ===================================================
echo   Starting HOUSEDATA Local Desktop Application
echo ===================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo Error: .venv virtual environment not found!
    echo Please run: uv venv --python 3.13 .venv
    pause
    exit /b 1
)

echo Applying database migrations...
.venv\Scripts\python.exe manage.py migrate --noinput

echo.
echo Starting web server on http://localhost:8080/ ...
start http://localhost:8080/
.venv\Scripts\python.exe manage.py runserver 8080

pause
