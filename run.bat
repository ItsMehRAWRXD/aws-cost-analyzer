@echo off
echo Starting AWS Cost Analyzer SaaS...
echo.

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and fill in your keys
    echo.
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Start the application
echo.
echo Starting server on http://localhost:5000
echo Press Ctrl+C to stop
echo.
python app.py