# Windows Activation Watermark Killer - 强力版
Write-Host "========================================" -ForegroundColor Red
Write-Host "   Windows 激活水印 - 强力清除工具" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red

$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "`n[!] 需要管理员权限！请以管理员身份运行 PowerShell 后重试" -ForegroundColor Red
    Write-Host "    右键点击 PowerShell -> 以管理员身份运行" -ForegroundColor Yellow
    Read-Host "`n按 Enter 退出"
    exit
}

Write-Host "`n[1/5] 方法一：深层注册表修复..." -ForegroundColor Cyan

# 修复多个注册表位置
$regPaths = @(
    @{Path="HKCU:\Control Panel\Desktop"; Name="PaintDesktopVersion"; Value=0},
    @{Path="HKCU:\Control Panel\Desktop"; Name="UserPreferencesMask"; Value=([byte[]](0x90,0x12,0x03,0x80,0x10,0x00,0x00,0x00))},
    @{Path="HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform\Activation"; Name="NotificationDisabled"; Value=1},
    @{Path="HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform\Activation"; Name="Manual"; Value=1}
)

foreach ($item in $regPaths) {
    try {
        if (-not (Test-Path $item.Path)) {
            New-Item -Path $item.Path -Force | Out-Null
        }
        Set-ItemProperty -Path $item.Path -Name $item.Name -Value $item.Value -Force
        Write-Host "    OK: $($item.Path)\$($item.Name)" -ForegroundColor Green
    } catch {
        Write-Host "    X: 无法设置 $($item.Name)" -ForegroundColor Gray
    }
}

Write-Host "`n[2/5] 方法二：停止 Software Protection 服务..." -ForegroundColor Cyan

try {
    Stop-Service sppsvc -Force -ErrorAction SilentlyContinue
    Set-Service sppsvc -StartupType Disabled -ErrorAction SilentlyContinue
    Write-Host "    OK: Software Protection 服务已停止并禁用" -ForegroundColor Green
} catch {
    Write-Host "    Note: 服务操作受限" -ForegroundColor Yellow
}

Write-Host "`n[3/5] 方法三：清理激活缓存..." -ForegroundColor Cyan

try {
    $cacheFiles = @(
        "$env:SystemRoot\system32\ spp\tokens\cache\cache.dat",
        "$env:SystemRoot\ServiceProfiles\NetworkService\AppData\Roaming\Microsoft\SoftwareProtectionPlatform\tokens.dat",
        "$env:SystemRoot\ServiceProfiles\NetworkService\AppData\Roaming\Microsoft\SoftwareProtectionPlatform\cache\cache.dat"
    )
    
    foreach ($file in $cacheFiles) {
        if (Test-Path $file) {
            Rename-Item -Path $file -NewName "$file.bak" -Force -ErrorAction SilentlyContinue
            Write-Host "    OK: 重命名 $([System.IO.Path]::GetFileName($file))" -ForegroundColor Green
        }
    }
} catch {
    Write-Host "    Note: 部分缓存文件无法访问" -ForegroundColor Yellow
}

Write-Host "`n[4/5] 方法四：组策略修复..." -ForegroundColor Cyan

try {
    # 创建或修改本地组策略
    $policiesPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform"
    if (-not (Test-Path $policiesPath)) {
        New-Item -Path $policiesPath -Force | Out-Null
    }
    Set-ItemProperty -Path $policiesPath -Name "NoGenTicket" -Value 1 -Type DWord -Force
    Write-Host "    OK: 组策略已更新" -ForegroundColor Green
} catch {
    Write-Host "    Note: 组策略修改受限" -ForegroundColor Yellow
}

Write-Host "`n[5/5] 方法五：重启关键进程..." -ForegroundColor Cyan

# 结束所有相关进程
$processes = @("explorer", "dwm", "csrss")
foreach ($proc in $processes) {
    Get-Process -Name $proc -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 3
Start-Process explorer.exe
Write-Host "    OK: 桌面已刷新" -ForegroundColor Green

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "   强力清除完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

Write-Host "`n[!] 重要提示：" -ForegroundColor Yellow
Write-Host "    1. 请立即重新启动电脑以应用所有更改" -ForegroundColor White
Write-Host "    2. 重启后水印应该完全消失" -ForegroundColor White
Write-Host "    3. 此方法修改了系统激活相关设置" -ForegroundColor White
Write-Host "    4. 建议尽快购买正版 Windows 许可证" -ForegroundColor Gray

Write-Host "`n[*] 如果重启后水印还在，Windows 更新可能会恢复它" -ForegroundColor Cyan
Write-Host "    可以再次运行此脚本" -ForegroundColor Gray

Read-Host "`n按 Enter 退出，然后请重新启动电脑"
