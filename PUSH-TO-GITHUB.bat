@echo off
cd /d %~dp0
echo Pushing AWS Cost Analyzer to GitHub...
echo.

git init
git add .
git commit -m "AWS Cost Analyzer SaaS - Production Ready"

echo.
echo Now create a new repo on GitHub and run:
echo git remote add origin https://github.com/YOUR_USERNAME/aws-cost-analyzer.git
echo git branch -M main
echo git push -u origin main
echo.
pause
