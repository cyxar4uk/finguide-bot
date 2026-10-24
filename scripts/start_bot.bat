@echo off
cd /d "%~dp0.."
chcp 65001 >nul
title FinGuide Bot Launcher

echo.
echo ========================================
echo      FinGuide Bot - Start Bot
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Install Python 3.12+ from https://www.python.org/
    pause
    exit /b 1
)

echo [INFO] Checking required libraries...
echo.

REM Check and install requirements
if exist "requirements.txt" (
    echo [INFO] Installing/updating dependencies...
    python -m pip install --upgrade pip >nul 2>&1
    python -m pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo [WARNING] Some packages failed to install
        echo [INFO] Trying to install critical packages...
        python -m pip install aiogram aiosqlite python-dotenv rapidfuzz beautifulsoup4 aiohttp --quiet
    )
    echo [OK] Dependencies checked
    echo.
) else (
    echo [WARNING] requirements.txt not found
    echo [INFO] Installing critical packages...
    python -m pip install aiogram aiosqlite python-dotenv rapidfuzz beautifulsoup4 aiohttp --quiet
    if errorlevel 1 (
        echo [ERROR] Failed to install packages
        pause
        exit /b 1
    )
    echo [OK] Critical packages installed
    echo.
)

REM Verify critical imports
echo [INFO] Verifying installation...
python -c "import aiogram, aiosqlite, dotenv, rapidfuzz, bs4, aiohttp" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Some required libraries are missing!
    echo [INFO] Please run: pip install -r requirements.txt
    pause
    exit /b 1
)
echo [OK] All libraries verified
echo.

REM Check .env file
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Create .env file based on .env.example
    pause
    exit /b 1
)

REM Check database
if not exist "finguide.db" (
    echo [INFO] Database not found. Creating...
    python seed_data.py
    if errorlevel 1 (
        echo [ERROR] Failed to create database
        pause
        exit /b 1
    )
    echo [OK] Database created
    echo.
)

echo [INFO] Starting FinGuide Bot...
echo [INFO] Press Ctrl+C to stop
echo.
echo ========================================
echo.

REM Start bot
python bot.py

REM If bot crashed
if errorlevel 1 (
    echo.
    echo [ERROR] Bot crashed!
    pause
)
