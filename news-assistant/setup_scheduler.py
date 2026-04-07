#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 定时任务设置脚本
设置每天早上8点和晚上8点自动运行
"""

import os
import sys
from pathlib import Path


def create_task_scheduler():
    """创建 Windows 任务计划程序任务"""
    
    # 获取路径
    script_dir = Path(__file__).parent.absolute()
    main_script = script_dir / "main.py"
    python_exe = sys.executable
    
    # 创建批处理文件
    morning_bat = script_dir / "run_morning.bat"
    evening_bat = script_dir / "run_evening.bat"
    
    # 早间批处理
    morning_content = f'''@echo off
cd /d "{script_dir}"
"{python_exe}" "{main_script}" --once
echo 早间新闻已推送
'''
    
    # 晚间批处理
    evening_content = f'''@echo off
cd /d "{script_dir}"
"{python_exe}" "{main_script}" --once --evening
echo 晚间新闻已推送
'''
    
    with open(morning_bat, 'w', encoding='gbk') as f:
        f.write(morning_content)
    
    with open(evening_bat, 'w', encoding='gbk') as f:
        f.write(evening_content)
    
    print(f"Batch files created:")
    print(f"  Morning: {morning_bat}")
    print(f"  Evening: {evening_bat}")
    
    # 创建 PowerShell 脚本来添加任务计划
    ps_script = script_dir / "create_tasks.ps1"
    ps_content = f'''
# 创建早间任务 (每天 8:00)
$morningAction = New-ScheduledTaskAction -Execute "{morning_bat}"
$morningTrigger = New-ScheduledTaskTrigger -Daily -At 08:00
$morningSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$morningPrincipal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive

Register-ScheduledTask -TaskName "新闻秘书-早间推送" `
    -Action $morningAction `
    -Trigger $morningTrigger `
    -Settings $morningSettings `
    -Principal $morningPrincipal `
    -Description "每天早上8点自动获取全球新闻并推送" `
    -Force

# 创建晚间任务 (每天 20:00)
$eveningAction = New-ScheduledTaskAction -Execute "{evening_bat}"
$eveningTrigger = New-ScheduledTaskTrigger -Daily -At 20:00
$eveningSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$eveningPrincipal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive

Register-ScheduledTask -TaskName "新闻秘书-晚间推送" `
    -Action $eveningAction `
    -Trigger $eveningTrigger `
    -Settings $eveningSettings `
    -Principal $eveningPrincipal `
    -Description "每天晚上8点自动获取全球新闻并推送" `
    -Force

Write-Host "Tasks created!" -ForegroundColor Green
Write-Host "Morning: 08:00 daily" -ForegroundColor Cyan
Write-Host "Evening: 20:00 daily" -ForegroundColor Cyan
'''
    
    with open(ps_script, 'w', encoding='utf-8') as f:
        f.write(ps_content)
    
    print(f"\nPowerShell script created: {ps_script}")
    print("\nRun as admin to create tasks:")
    print(f"  powershell -ExecutionPolicy Bypass -File \"{ps_script}\"")
    
    return ps_script


def remove_tasks():
    """删除定时任务"""
    os.system('schtasks /delete /tn "新闻秘书-早间推送" /f')
    os.system('schtasks /delete /tn "新闻秘书-晚间推送" /f')
    print("定时任务已删除")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--remove', action='store_true', help='删除定时任务')
    args = parser.parse_args()
    
    if args.remove:
        print("Tasks removed")
    else:
        ps_script = create_task_scheduler()
        
        # 询问是否立即运行
        print("\nRun test now? (y/n): ")
        response = input().strip().lower()
        if response == 'y':
            import subprocess
            script_dir = Path(__file__).parent
            subprocess.run([sys.executable, str(script_dir / "main.py"), "--once", "--force"])
