@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 微博V+问答抓取工具
py weibo_vplus_scraper_v3.py
pause
