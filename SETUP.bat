@echo off
cd /d %~dp0
echo Installing AWS Cost Analyzer SaaS...
echo.
pip install flask python-dotenv stripe
echo.
echo Setup complete! Edit .env file with your keys, then run LAUNCH.bat
pause
