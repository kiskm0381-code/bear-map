@echo off
echo ==================================================
echo   Bear Alert Hokkaido - Sync System
echo ==================================================
echo.
echo [1/3] Fetching latest bear data from Hokkaido...
python scripts/fetch_data.py

echo.
echo [2/3] Preparing data for Web (Git Commit)...
git add .
git commit -m "Automated update"

echo.
echo [3/3] Uploading to GitHub (Public Web Map)...
git push origin main

echo.
echo ==================================================
echo   SUCCESS! 
echo   Please refresh your browser in 1-2 minutes.
echo ==================================================
pause
