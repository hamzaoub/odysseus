@echo off
echo =========================================
echo Starting Odysseus Workspace Setup & Run
echo =========================================

:: Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo [1/5] Creating virtual environment...
    python -m venv venv
) else (
    echo [1/5] Virtual environment already exists, skipping creation.
)

:: Activate the virtual environment
echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install requirements
echo [3/5] Installing dependencies...
pip install -r requirements.txt

:: Run the setup script
echo [4/5] Running setup...
python setup.py

:: Start the server
echo [5/5] Starting Odysseus server...
echo Server will be available at http://localhost:7000
python -m uvicorn app:app --host 0.0.0.0 --port 7000

pause
