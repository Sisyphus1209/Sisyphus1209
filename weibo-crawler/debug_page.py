#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本：查看微博文章列表页的结构
"""

from pathlib import Path
from playwright.sync_api import sync_playwright

STORAGE_STATE_FILE = Path("output/weibo_storage_state.json").resolve()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
    context = browser.new_context(
        viewport={'width': 1280, 'height': 900},
        storage_state=str(STORAGE_STATE_FILE)
    )
    page = context.new_page()
    
    print("正在打开页面...")
    page.goto("https://weibo.com/1039916297?tabtype=article", timeout=30000)
    page.wait_for_timeout(5000)
    
    print("\n=== 所有链接（含 /ttarticle /status 等） ===")
    links = page.evaluate("""() => {
        const result = [];
        document.querySelectorAll('a[href]').forEach(a => {
            const href = a.href;
            const text = a.innerText.trim();
            if (href.includes('/ttarticle') || href.includes('/status') || href.includes('weibo.com')) {
                if (text.length > 5 && text.length < 200) {
                    result.push({href, text: text.substring(0, 60)});
                }
            }
        });
        return result.slice(0, 20);
    }""")
    
    for i, link in enumerate(links, 1):
        print(f"{i}. [{link['text']}] -> {link['href']}")
    
    print("\n=== 按回车关闭浏览器 ===")
    input()
    browser.close()
