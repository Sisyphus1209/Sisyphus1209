@echo off
chcp 65001 >nul
echo ==========================================
echo  重置登录状态
echo ==========================================
echo.

cd /d "%~dp0"

echo 正在删除登录状态文件...

if exist "output\weibo_storage_state.json" (
    del "output\weibo_storage_state.json"
    echo [OK] 已删除 weibo_storage_state.json
) else (
    echo [INFO] weibo_storage_state.json 不存在
)

if exist "output\weibo_cookies.json" (
    del "output\weibo_cookies.json"
    echo [OK] 已删除 weibo_cookies.json
) else (
    echo [INFO] weibo_cookies.json 不存在
)

echo.
echo [OK] 登录状态已重置！
echo.
echo 下次运行脚本时需要重新扫码登录。
echo.

pause
