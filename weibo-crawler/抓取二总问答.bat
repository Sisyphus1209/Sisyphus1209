@echo off
chcp 936 >nul
echo ==========================================
echo  Weibo V+ QA Scraper v3.0
echo ==========================================
echo.

cd /d "%~dp0"

echo Current directory: %cd%
echo.

echo Checking Python...
py --version
echo.

echo Starting script...
echo.

py weibo_vplus_scraper_v3.py

echo.
echo Script finished with exit code: %errorlevel%
echo.

if %errorlevel% neq 0 (
    echo [ERROR] Script execution failed!
    echo Please check the error messages above
    echo.
)

echo Press any key to exit...
pause >nul
