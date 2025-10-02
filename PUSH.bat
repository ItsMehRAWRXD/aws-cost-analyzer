@echo off
cd /d %~dp0
echo Pushing to GitHub...
git config --global user.email "rawrxd@github.com"
git config --global user.name "ItsMehRAWRXD"
git init
git add .
git commit -m "AWS Cost Analyzer SaaS - Production Ready"
git branch -M main
git remote add origin https://github.com/ItsMehRAWRXD/aws-cost-analyzer.git
git push -u origin main
echo.
echo Done! Repo live at: https://github.com/ItsMehRAWRXD/aws-cost-analyzer
pause
