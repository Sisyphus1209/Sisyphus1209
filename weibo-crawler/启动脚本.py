#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动器 - 运行微博V+问答抓取脚本
"""

import subprocess
import sys
from pathlib import Path

def main():
    print("=" * 60)
    print(" 微博 V+ 问答抓取工具 v3.0")
    print("=" * 60)
    print()
    
    # 确保在正确目录
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print(f"当前目录: {Path.cwd()}")
    print()
    
    # 运行主脚本
    try:
        subprocess.run([sys.executable, "weibo_vplus_scraper_v3.py"])
    except subprocess.CalledProcessError as e:
        print(f"\n[错误] 脚本执行失败，退出码: {e.returncode}")
    except KeyboardInterrupt:
        print("\n[信息] 用户中断")
    
    print()
    input("按回车键退出...")

if __name__ == "__main__":
    import os
    main()
