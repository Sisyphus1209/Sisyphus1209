@echo off
echo ==========================================
echo    AI News Assistant
echo ==========================================
echo.
echo [1] Get Morning News
echo [2] Get Evening News
echo [3] Start Scheduler Service
echo [4] Setup Daily Tasks
echo [5] Refresh Weibo Search (Login required)
echo [6] Exit
echo.
set /p choice="Select (1-6): "

if "%choice%"=="1" goto morning
if "%choice%"=="2" goto evening
if "%choice%"=="3" goto service
if "%choice%"=="4" goto schedule
if "%choice%"=="5" goto weibo
if "%choice%"=="6" goto end

echo Invalid choice.
pause
exit

:morning
echo.
echo Fetching morning news...
python "%~dp0main.py" --once --force
echo.
echo Done! Report opened.
pause
exit

:evening
echo.
echo Fetching evening news...
python "%~dp0main.py" --once --evening --force
echo.
echo Done! Report opened.
pause
exit

:service
echo.
echo Starting scheduler...
echo Press Ctrl+C to stop
echo.
python "%~dp0main.py"
pause
exit

:schedule
echo.
echo Setting up scheduled tasks...
echo Admin permission required...
echo.
powershell -Command "Start-Process powershell -Verb runAs -ArgumentList '-ExecutionPolicy Bypass -File \"%~dp0setup_scheduler.py\"'"
echo.
echo Please complete setup in the admin window.
pause
exit

:weibo
echo.
echo Refreshing Weibo search data...
echo This will open a browser for login if cookie is expired.
python "%~dp0weibo_searcher.py"
echo.
echo Done! Weibo results updated.
pause
exit

:end
exit
