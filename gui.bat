@echo off
ECHO "--- Setting up environment for GUI App ---"

REM Check if the venv directory exists
IF NOT EXIST ".\venv" (
    ECHO "Virtual environment not found. Creating one..."
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        ECHO "Error: Failed to create virtual environment. Please ensure Python is installed and in your PATH."
        pause
        exit /b
    )
)

ECHO "Activating virtual environment..."
CALL ".\venv\Scripts\activate.bat"

ECHO "Installing required packages..."
pip install requests Pillow google-generativeai selenium webdriver-manager

ECHO "--- Setup complete. Launching application... ---"
python gui_app.py

ECHO "--- Application closed. ---"
pause