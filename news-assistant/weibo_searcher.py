#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weibo Searcher for News Assistant
Uses Playwright to search Weibo for tech/MCP/CLI/skills content.
Reuses storage_state from weibo_crawler if available.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict

STORAGE_STATE_PATH = Path(r"C:\Users\Administrator\weibo_crawler\output\weibo_storage_state.json")
RESULTS_PATH = Path(__file__).parent / "weibo_results.json"

# Keywords to search on Weibo
SEARCH_KEYWORDS = ["MCP", "AI工具", "开源技能", "CLI神器", "编程技巧"]


def search_weibo_with_playwright() -> List[Dict]:
    """
    Search Weibo using Playwright with stored login state.
    Falls back to empty list if not logged in.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[Weibo] Playwright not installed. Run: pip install playwright")
        return []

    if not STORAGE_STATE_PATH.exists():
        print(f"[Weibo] No login state found at {STORAGE_STATE_PATH}")
        print("[Weibo] Please run weibo_crawler login first.")
        return []

    results = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        try:
            context = browser.new_context(storage_state=str(STORAGE_STATE_PATH))
        except Exception as e:
            print(f"[Weibo] Failed to load storage state: {e}")
            browser.close()
            return []
        
        page = context.new_page()
        
        login_refreshed = False
        
        for keyword in SEARCH_KEYWORDS:
            print(f"[Weibo] Searching: {keyword} ...")
            try:
                # Use mobile search URL
                encoded = keyword
                url = f"https://s.weibo.com/weibo?q={encoded}"
                page.goto(url, timeout=20000)
                page.wait_for_timeout(3000)  # Wait for JS render
                
                # Check if login required
                if page.locator('text=登录').count() > 0 and page.locator('.card-wrap').count() == 0:
                    print(f"[Weibo] Login required for search. Cookie may be expired.")
                    if not login_refreshed:
                        print("[Weibo] Opening browser for manual login...")
                        print("[Weibo] Please scan QR code with Weibo APP. Waiting 60 seconds...")
                        browser.close()
                        # Re-launch visible browser for login
                        vis_browser = p.chromium.launch(headless=False)
                        vis_context = vis_browser.new_context()
                        vis_page = vis_context.new_page()
                        vis_page.goto('https://weibo.com/login.php', timeout=30000)
                        vis_page.wait_for_timeout(60000)  # Give user 60s to login
                        vis_context.storage_state(path=str(STORAGE_STATE_PATH))
                        vis_browser.close()
                        print(f"[Weibo] New login state saved to {STORAGE_STATE_PATH}")
                        # Restart with new state
                        browser = p.chromium.launch(headless=True)
                        context = browser.new_context(storage_state=str(STORAGE_STATE_PATH))
                        page = context.new_page()
                        login_refreshed = True
                        # Retry this keyword
                        page.goto(url, timeout=20000)
                        page.wait_for_timeout(3000)
                    else:
                        continue
                
                # Extract weibo cards
                cards = page.locator('.card-wrap').all()[:5]
                for card in cards:
                    try:
                        text_el = card.locator('.txt').first
                        text = text_el.inner_text() if text_el.count() > 0 else ""
                        text = text.strip().replace('\n', ' ')[:300]
                        
                        if not text or len(text) < 10:
                            continue
                        
                        # Filter: must be tech/MCP/CLI related
                        lower = text.lower()
                        if not any(k in lower or k in text for k in [
                            'mcp', 'skill', 'cli', 'ai', '工具', '开源', 
                            '编程', '代码', '大模型', 'chatgpt', 'kimi', 'claude'
                        ]):
                            continue
                        
                        # Try to get link
                        link_el = card.locator('a[node-type="feed_list_item_date"]').first
                        href = link_el.get_attribute('href') if link_el.count() > 0 else ""
                        
                        results.append({
                            "title": f"[微博] {text[:60]}",
                            "summary": text,
                            "source": "微博搜索",
                            "keyword": keyword,
                            "link": href or "https://s.weibo.com",
                            "time": datetime.now().isoformat()
                        })
                        
                    except Exception:
                        continue
                
                time.sleep(2)  # Be polite
                
            except Exception as e:
                print(f"[Weibo] Error searching '{keyword}': {e}")
                continue
        
        browser.close()
    
    # Save results
    with open(RESULTS_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"[Weibo] Found {len(results)} relevant posts.")
    return results


def load_weibo_results() -> List[Dict]:
    """Load cached weibo search results."""
    if not RESULTS_PATH.exists():
        return []
    try:
        with open(RESULTS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


if __name__ == "__main__":
    posts = search_weibo_with_playwright()
    for p in posts[:5]:
        print(f"- {p['title']}")
