@echo off
echo ==========================================
echo    设置 Obsidian 为默认 Markdown 阅读器
echo ==========================================
echo.

:: 检查 Obsidian 安装路径
if exist "D:\Obsidian\Obsidian.exe" (
    set OBSIDIAN_PATH=D:\Obsidian\Obsidian.exe
    echo 找到 Obsidian: D:\Obsidian\
) else if exist "C:\Users\%USERNAME%\AppData\Local\Obsidian\Obsidian.exe" (
    set OBSIDIAN_PATH=C:\Users\%USERNAME%\AppData\Local\Obsidian\Obsidian.exe
    echo 找到 Obsidian: %OBSIDIAN_PATH%
) else (
    echo 未找到 Obsidian，请先安装或手动设置路径
    pause
    exit
)

echo.
echo 正在设置 .md 文件默认打开方式...
echo.

:: 注册 Obsidian 为 Markdown 编辑器
reg add "HKCU\Software\Classes\.md" /ve /d "Obsidian.md" /f
reg add "HKCU\Software\Classes\Obsidian.md\shell\open\command" /ve /d "\"%OBSIDIAN_PATH%\" \"%%1\"" /f

echo ✅ 设置完成！
echo.
echo 现在双击 .md 文件将用 Obsidian 打开
echo.
pause
