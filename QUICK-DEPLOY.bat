@echo off
cd /d %~dp0
echo AWS Cost Analyzer - Quick Deploy to Render.com
echo.
echo Step 1: Initialize Git
git init
git add .
git commit -m "Initial deployment"
echo.
echo Step 2: Create GitHub repo and push
echo Run these commands:
echo   git remote add origin YOUR_GITHUB_REPO_URL
echo   git push -u origin main
echo.
echo Step 3: Go to render.com
echo   - Sign up/login
echo   - Click "New +" and select "Web Service"
echo   - Connect your GitHub repo
echo   - Render will auto-detect render.yaml
echo   - Add your Stripe keys in Environment
echo   - Click "Create Web Service"
echo.
echo Done! Your SaaS will be live in 2 minutes!
pause
