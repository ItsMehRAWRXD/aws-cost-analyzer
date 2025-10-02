@echo off
cd /d %~dp0
echo Force pushing to GitHub...
git push -f origin main
echo.
echo Done! Check: https://github.com/ItsMehRAWRXD/aws-cost-analyzer
pause
