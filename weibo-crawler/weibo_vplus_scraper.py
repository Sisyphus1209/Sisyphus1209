#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微博 V+ 问答抓取脚本
"""

import asyncio
import json
import os
import time
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# 配置
TARGET_UID = "1039916297"
LIST_URL = f"https://weibo.com/{TARGET_UID}?tabtype=article"
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class WeiboVPlusScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.qa_data = []
        
    async def start(self):
        print("=" * 60)
        print("微博 V+ 问答抓取工具")
        print("=" * 60)
        print()
        
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0'
        )
        
        self.page = await self.context.new_page()
        
        # 加载已保存的登录状态
        cookies_file = OUTPUT_DIR / "weibo_cookies.json"
        if cookies_file.exists():
            print("发现已保存的登录状态，正在加载...")
            try:
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                await self.context.add_cookies(cookies)
                print("登录状态加载完成！")
                return True
            except Exception as e:
                print(f"加载登录状态失败: {e}")
        
        return False
    
    async def login_with_qr(self):
        print("\n" + "=" * 60)
        print("请使用微博手机 APP 扫描二维码登录")
        print("=" * 60)
        print()
        
        await self.page.goto("https://weibo.com/login.php")
        await self.page.wait_for_timeout(3000)
        
        print("等待二维码加载...")
        print("\n请在 60 秒内完成扫码")
        
        try:
            await self.page.wait_for_url(lambda url: "weibo.com/login" not in url and "weibo.com" in url, timeout=60000)
            print("[OK] 登录成功！")
            
            cookies = await self.context.cookies()
            with open(OUTPUT_DIR / "weibo_cookies.json", 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            print("登录状态已保存")
            
            return True
            
        except Exception as e:
            print(f"[ERROR] 登录超时或失败: {e}")
            return False
    
    async def get_qa_links_from_list(self):
        print("\n" + "=" * 60)
        print("正在获取问答列表...")
        print("=" * 60)
        
        await self.page.goto(LIST_URL)
        print(f"当前页面: {self.page.url}")
        print("等待页面加载...")
        await self.page.wait_for_timeout(10000)
        
        # 保存截图看看页面
        screenshot_path = OUTPUT_DIR / "debug_list_page.png"
        await self.page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"已保存页面截图: {screenshot_path}")
        
        # 获取所有链接
        all_links = await self.page.query_selector_all('a[href]')
        print(f"页面上共有 {len(all_links)} 个链接")
        
        qa_links = []
        for link in all_links:
            try:
                href = await link.get_attribute('href')
                if href and isinstance(href, str):
                    # 检查是否是文章/问答链接
                    if 'article' in href.lower() or ('/p/' in href and 'weibo' in href):
                        # 处理相对链接
                        if href.startswith('//'):
                            href = 'https:' + href
                        elif href.startswith('/'):
                            href = 'https://weibo.com' + href
                        
                        if href not in qa_links:
                            qa_links.append(href)
            except:
                continue
        
        print(f"\n共找到 {len(qa_links)} 个文章链接")
        
        # 显示前10个
        if qa_links:
            print("\n前10个链接:")
            for i, link in enumerate(qa_links[:10], 1):
                print(f"  {i}. {link}")
        
        return qa_links
    
    async def scrape_single_qa(self, url, index, total):
        print(f"\n[{index}/{total}] 处理: {url}")
        
        try:
            await self.page.goto(url)
            await self.page.wait_for_timeout(3000)
            
            # 获取页面标题
            title = await self.page.title()
            print(f"  页面标题: {title}")
            
            # 查找"免费围观"按钮
            page_content = await self.page.content()
            
            # 尝试点击"免费围观"
            btn_clicked = False
            for btn_text in ['免费围观', '免费观看', '围观']:
                try:
                    btn = await self.page.query_selector(f'text={btn_text}')
                    if btn:
                        print(f"  发现'{btn_text}'按钮")
                        
                        # 尝试取消勾选"分享到微博"
                        try:
                            checkbox = await self.page.query_selector('input[type="checkbox"]')
                            if checkbox:
                                await checkbox.click()
                                print("  已取消勾选")
                                await self.page.wait_for_timeout(500)
                        except:
                            pass
                        
                        await btn.click()
                        print(f"  已点击'{btn_text}'")
                        await self.page.wait_for_timeout(3000)
                        btn_clicked = True
                        break
                except:
                    continue
            
            if not btn_clicked:
                print("  未找到按钮，可能已展开")
            
            # 提取内容
            content = await self.page.content()
            
            # 获取可见文本
            text_content = await self.page.evaluate('''() => {
                const main = document.querySelector('article') || 
                            document.querySelector('[role="main"]') ||
                            document.body;
                return main.innerText;
            }''')
            
            qa_item = {
                'index': index,
                'url': url,
                'title': title,
                'content': text_content[:5000] if text_content else "",  # 限制长度
                'crawled_at': datetime.now().isoformat()
            }
            
            print(f"  [OK] 抓取成功，内容长度: {len(text_content) if text_content else 0}")
            
            return qa_item
            
        except Exception as e:
            print(f"  [ERROR] 抓取失败: {e}")
            return {
                'index': index,
                'url': url,
                'error': str(e),
                'crawled_at': datetime.now().isoformat()
            }
    
    async def scrape_all_qa(self, qa_links):
        print("\n" + "=" * 60)
        print("开始逐个抓取")
        print("=" * 60)
        
        total = len(qa_links)
        # 限制最多抓5个测试
        test_limit = min(5, total)
        print(f"本次测试只抓前 {test_limit} 个\n")
        
        for i, url in enumerate(qa_links[:test_limit], 1):
            qa_item = await self.scrape_single_qa(url, i, test_limit)
            if qa_item:
                self.qa_data.append(qa_item)
            
            await asyncio.sleep(2)
        
        return self.qa_data
    
    async def save_data(self, qa_items):
        print("\n" + "=" * 60)
        print("保存数据")
        print("=" * 60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存为 JSON
        json_file = OUTPUT_DIR / f"erzong_qa_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(qa_items, f, ensure_ascii=False, indent=2)
        print(f"[OK] JSON: {json_file}")
        
        # 保存为文本
        txt_file = OUTPUT_DIR / f"erzong_qa_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"二总 V+ 问答\n")
            f.write(f"抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"数量: {len(qa_items)}\n")
            f.write("=" * 60 + "\n\n")
            
            for item in qa_items:
                f.write(f"【{item['index']}】{item['title']}\n")
                f.write(f"URL: {item['url']}\n")
                if 'error' in item:
                    f.write(f"错误: {item['error']}\n")
                else:
                    f.write(f"\n{item['content']}\n")
                f.write("\n" + "=" * 60 + "\n\n")
        
        print(f"[OK] TXT: {txt_file}")
        
        return json_file, txt_file
    
    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


async def main():
    scraper = WeiboVPlusScraper()
    
    try:
        logged_in = await scraper.start()
        
        if not logged_in:
            login_success = await scraper.login_with_qr()
            if not login_success:
                print("登录失败，退出")
                return
        
        # 获取问答链接
        qa_links = await scraper.get_qa_links_from_list()
        
        if not qa_links:
            print("\n未找到任何链接，请检查截图")
            input("\n按回车键关闭...")
            return
        
        print(f"\n找到 {len(qa_links)} 个链接")
        input("\n按回车键开始抓取（测试只抓前5个）...")
        
        # 抓取
        qa_items = await scraper.scrape_all_qa(qa_links)
        
        # 保存
        if qa_items:
            files = await scraper.save_data(qa_items)
            print("\n" + "=" * 60)
            print("完成！")
            print("=" * 60)
            for f in files:
                print(f"  {f}")
        
        input("\n按回车键关闭浏览器...")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键关闭...")
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
