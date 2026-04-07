@echo off
chcp 936 >nul
echo ==========================================
echo  强制重新登录
echo ==========================================
echo.
echo Deleting saved login state...
if exist "output\weibo_storage_state.json" del "output\weibo_storage_state.json"
echo.
echo Done! Now starting scraper...
echo.
py weibo_vplus_scraper_v3.py
echo.
pause
