@echo off
REM KUYAN - Setup and Run Script (Windows)
REM This script creates a virtual environment, installs dependencies, and runs the app

echo ======================================
echo KUYAN - Setup and Run
echo ======================================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Python is not installed
    echo Please install Python 3.11 or higher from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "venv\" (
    echo Virtual environment already exists
) else (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
)

echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Virtual environment activated
echo.

REM Check if dependencies are installed
if exist "venv\Lib\site-packages\streamlit\__init__.py" (
    echo Dependencies already installed
) else (
    echo Installing dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    echo Dependencies installed
)

echo.
echo ======================================
echo Starting KUYAN...
echo ======================================
echo.
echo Production Mode: http://localhost:8502
echo Sandbox Mode:    http://localhost:8502/?mode=sandbox
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run Streamlit on port 8502 (for local development)
streamlit run app.py --server.port 8502
