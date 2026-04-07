# 移除 Windows 激活水印脚本
# 注意：这只是临时隐藏水印，建议购买正版 Windows 激活

Write-Host "正在尝试移除 Windows 激活水印..." -ForegroundColor Yellow
Write-Host "注意：这只是临时方案，建议购买正版 Windows 许可证激活" -ForegroundColor Cyan

# 方法1：修改注册表（临时方案）
try {
    # 创建或修改 PaintDesktopVersion 键值
    $regPath = "HKCU:\Control Panel\Desktop"
    
    # 检查并设置 PaintDesktopVersion 为 0
    $currentValue = Get-ItemProperty -Path $regPath -Name "PaintDesktopVersion" -ErrorAction SilentlyContinue
    
    if ($currentValue) {
        Set-ItemProperty -Path $regPath -Name "PaintDesktopVersion" -Value 0
        Write-Host "✓ 已修改注册表设置" -ForegroundColor Green
    } else {
        New-ItemProperty -Path $regPath -Name "PaintDesktopVersion" -Value 0 -PropertyType DWORD
        Write-Host "✓ 已创建注册表键值" -ForegroundColor Green
    }
    
    # 方法2：使用 slmgr 重新注册（可能需要管理员权限）
    Write-Host "`n正在尝试刷新 Windows 激活状态..." -ForegroundColor Yellow
    
    # 这些命令需要管理员权限
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
    
    if ($isAdmin) {
        # 停止 Software Protection 服务
        Stop-Service sppsvc -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        
        # 启动服务
        Start-Service sppsvc -ErrorAction SilentlyContinue
        
        Write-Host "✓ 已刷新 Software Protection 服务" -ForegroundColor Green
    } else {
        Write-Host "⚠ 未以管理员权限运行，某些操作可能无效" -ForegroundColor Yellow
        Write-Host "  建议：右键 PowerShell 选择'以管理员身份运行'后再次执行此脚本" -ForegroundColor Gray
    }
    
    # 方法3：重启 Explorer
    Write-Host "`n正在重启资源管理器以应用更改..." -ForegroundColor Yellow
    
    Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Start-Process explorer
    
    Write-Host "✓ 资源管理器已重启" -ForegroundColor Green
    
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "操作完成！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "如果水印仍然存在，请尝试：" -ForegroundColor Yellow
    Write-Host "1. 重新启动电脑" -ForegroundColor White
    Write-Host "2. 以管理员身份运行此脚本" -ForegroundColor White
    Write-Host "3. 检查 Windows 更新" -ForegroundColor White
    Write-Host "`n⚠ 提示：这只是临时隐藏水印" -ForegroundColor Red
    Write-Host "   建议购买正版 Windows 许可证进行永久激活" -ForegroundColor Gray
    
} catch {
    Write-Host "❌ 发生错误: $_" -ForegroundColor Red
}

Read-Host "`n按 Enter 键退出"
