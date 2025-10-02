@echo off
REM AWS Cost SaaS - Quick Start Script for Windows
REM This script sets up and runs the complete SaaS application

echo 🚀 AWS Cost SaaS - Quick Start
echo ================================

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found!
    echo 📋 Copying env.template to .env...
    copy env.template .env
    echo ✅ Please edit .env with your actual values before continuing
    echo 🔧 Required: DATABASE_URL, JWT_SECRET_KEY, STRIPE keys, AWS credentials
    echo.
    pause
)

REM Check if virtual environment exists
if not exist "venv" (
    echo 🐍 Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📦 Installing dependencies...
pip install -r requirements.txt

REM Start the application
echo 🚀 Starting AWS Cost SaaS...
echo 📱 Frontend: http://localhost:8000
echo 🔧 API Docs: http://localhost:8000/docs
echo ❤️  Health: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server
echo.

cd backend
python main.py
