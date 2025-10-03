@echo off
REM Quick Start Script for Multiprocessing Server Demo
REM This script sets up and runs a complete demonstration

echo ==========================================
echo Multiprocessing Server Quick Start
echo ==========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

echo ==========================================
echo Setup complete! Choose an option:
echo ==========================================
echo 1. Run basic demo (single client, 1kHz)
echo 2. Run multiprocess demo (4 clients, 2kHz each)
echo 3. Run stress test (8 clients, 1kHz each)
echo 4. Run automated test suite
echo 5. Start server only
echo 6. Start client simulator only
echo ==========================================

set /p choice="Enter your choice (1-6): "

if "%choice%"=="1" (
    echo Running basic demo...
    python run_demo.py --scenario basic
) else if "%choice%"=="2" (
    echo Running multiprocess demo...
    python run_demo.py --scenario multiprocess
) else if "%choice%"=="3" (
    echo Running stress test...
    python run_demo.py --scenario stress
) else if "%choice%"=="4" (
    echo Running automated test suite...
    python test_runner.py
) else if "%choice%"=="5" (
    echo Starting server...
    python server.py
) else if "%choice%"=="6" (
    echo Starting client simulator...
    python client_simulator.py
) else (
    echo Invalid choice. Exiting.
    pause
    exit /b 1
)

echo ==========================================
echo Done!
echo ==========================================
pause
