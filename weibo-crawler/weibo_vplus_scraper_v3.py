#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
"""
微博 V+ 问答抓取脚本 - v3.0 手动控制版
使用方法：
1. 运行脚本，扫码登录
2. 在浏览器中手动进入二总的文章列表页
3. 按回车键，脚本提取链接
4. 脚本逐个抓取问答内容
"""

import asyncio
import json
import re
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_STATE_FILE = OUTPUT_DIR / "weibo_storage_state.json"


class WeiboVPlusScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.qa_data = []
        
    async def start(self):
        print("=" * 60)
        print(" 微博 V+ 问答抓取工具 v3.0 ")
        print("=" * 60)
        print()
        
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        # 加载登录状态
        storage_state = None
        if STORAGE_STATE_FILE.exists():
            try:
                with open(STORAGE_STATE_FILE, 'r', encoding='utf-8') as f:
                    storage_state = json.load(f)
                print("[OK] 已加载保存的登录状态")
            except Exception as e:
                print(f"[WARN] 加载登录状态失败: {e}")
        
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0',
            storage_state=storage_state
        )
        
        self.page = await self.context.new_page()
        
        return storage_state is not None
    
    async def save_storage_state(self):
        try:
            storage_state = await self.context.storage_state()
            with open(STORAGE_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(storage_state, f, ensure_ascii=False, indent=2)
            print("[OK] 登录状态已保存，下次无需扫码")
        except Exception as e:
            print(f"[WARN] 保存登录状态失败: {e}")
    
    async def login(self):
        print("\n" + "-" * 60)
        print(" 步骤1: 登录")
        print("-" * 60)
        print()
        print("1. 在浏览器中完成扫码登录")
        print("2. 登录成功后，在浏览器中手动进入二总的文章列表页")
        print("   URL: https://weibo.com/1039916297?tabtype=article")
        print("3. 然后回到这里按回车键继续")
        print()
        
        await self.page.goto("https://weibo.com/login.php")
        
        input(">>> 完成上述步骤后，按回车键继续...")
        
        # 保存登录状态
        await self.save_storage_state()
        
        print(f"\n当前页面: {self.page.url}")
        return True
    
    async def extract_links(self):
        print("\n" + "-" * 60)
        print(" 步骤2: 提取问答链接")
        print("-" * 60)
        print()
        
        # 让用户滚动加载所有内容
        print(">>> 请在浏览器中滚动页面，确保所有问答都已加载 <<<")
        input(">>> 完成后，按回车键提取链接...")
        
        # 提取文章链接
        links = await self.page.evaluate('''() => {
            const result = [];
            const seen = new Set();
            
            // 找所有文章链接
            document.querySelectorAll('a[href*="/ttarticle/p/show"]').forEach(a => {
                const url = a.href;
                if (url && !seen.has(url)) {
                    seen.add(url);
                    result.push({
                        url: url,
                        title: a.innerText.trim().substring(0, 60)
                    });
                }
            });
            
            return result;
        }''')
        
        print(f"\n[✓] 找到 {len(links)} 个问答链接")
        
        if not links:
            return []
        
        # 显示前5个
        print("\n前5个问答:")
        for i, link in enumerate(links[:5], 1):
            print(f"  {i}. {link['title'][:50]}...")
        
        if len(links) > 5:
            print(f"  ... 还有 {len(links) - 5} 个")
        
        print(f"\n>>> 确认要抓取这 {len(links)} 个问答吗？<<<")
        input(">>> 按回车键开始抓取，或关闭窗口取消...")
        
        return [l['url'] for l in links]
    
    async def scrape_qa(self, url, index, total):
        print(f"\n[{index}/{total}] 正在抓取...")
        print(f"  URL: {url[:70]}...")
        
        try:
            # 在新标签页打开
            new_page = await self.context.new_page()
            await new_page.goto(url, wait_until="networkidle", timeout=30000)
            await new_page.wait_for_timeout(3000)
            
            title = await new_page.title()
            print(f"  标题: {title[:50]}...")
            
            # 检查是否需要点击"免费围观"
            content = await new_page.content()
            need_click = '免费围观' in content or '免费观看' in content
            
            if need_click:
                print("  [WARN] 需要点击'免费围观'按钮")
                print("  >>> 请在浏览器中：")
                print("      1. 取消'分享到微博'的勾选")
                print("      2. 点击'免费围观'按钮")
                print("      3. 等待答案显示后，回到这里按回车键")
                input()
                await new_page.wait_for_timeout(2000)
            
            # 提取内容
            data = await self.extract_content(new_page)
            
            await new_page.close()
            
            item = {
                'index': index,
                'url': url,
                'title': title,
                'question': data.get('question', ''),
                'answer': data.get('answer', ''),
                'time': data.get('time', ''),
                'crawled_at': datetime.now().isoformat()
            }
            
            print(f"  [OK] 完成，内容长度: {len(item['answer'])}")
            return item
            
        except Exception as e:
            print(f"  [ERROR] 失败: {e}")
            return {
                'index': index,
                'url': url,
                'error': str(e),
                'crawled_at': datetime.now().isoformat()
            }
    
    async def extract_content(self, page):
        return await page.evaluate('''() => {
            const r = { question: '', answer: '', time: '' };
            
            // 标题作为问题
            const h1 = document.querySelector('h1');
            if (h1) r.question = h1.innerText.trim();
            
            // 正文内容
            const selectors = [
                '.article-content',
                '[class*="article-body"]',
                'article',
                '.WB_detail',
                '[class*="content"]'
            ];
            
            for (let sel of selectors) {
                const el = document.querySelector(sel);
                if (el && el.innerText.length > 100) {
                    r.answer = el.innerText.trim();
                    break;
                }
            }
            
            // 时间
            const timeEl = document.querySelector('time, [class*="time"]');
            if (timeEl) r.time = timeEl.innerText.trim();
            
            return r;
        }''')
    
    async def scrape_all(self, links):
        print("\n" + "-" * 60)
        print(" 步骤3: 抓取问答内容")
        print("-" * 60)
        
        for i, url in enumerate(links, 1):
            item = await self.scrape_qa(url, i, len(links))
            self.qa_data.append(item)
            await asyncio.sleep(2)
        
        return self.qa_data
    
    async def save(self):
        print("\n" + "-" * 60)
        print(" 步骤4: 保存数据")
        print("-" * 60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        json_file = OUTPUT_DIR / f"erzong_qa_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.qa_data, f, ensure_ascii=False, indent=2)
        print(f"[✓] JSON: {json_file}")
        
        # Markdown
        md_file = OUTPUT_DIR / f"erzong_qa_{timestamp}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# 二总 V+ 问答\n\n")
            f.write(f"抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"数量: {len(self.qa_data)}\n\n---\n\n")
            
            for item in self.qa_data:
                f.write(f"## 【{item['index']}】{item.get('title', '无标题')}\n\n")
                f.write(f"**链接**: {item['url']}\n\n")
                if item.get('time'):
                    f.write(f"**时间**: {item['time']}\n\n")
                
                if 'error' in item:
                    f.write(f"> ⚠️ 错误: {item['error']}\n\n")
                else:
                    if item.get('question'):
                        f.write(f"### 问题\n\n{item['question']}\n\n")
                    if item.get('answer'):
                        f.write(f"### 回答\n\n{item['answer']}\n\n")
                
                f.write("---\n\n")
        
        print(f"[✓] Markdown: {md_file}")
        return json_file, md_file
    
    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


async def main():
    scraper = WeiboVPlusScraper()
    
    try:
        # 启动
        has_login = await scraper.start()
        
        if has_login:
            print("\n[WARN] 检测到保存的登录状态，但可能已过期")
            print(">>> 按回车键尝试使用保存的登录状态")
            print(">>> 或关闭窗口，删除 output/weibo_storage_state.json 后重新运行")
            input()
            
            # 验证登录是否有效
            print("\n正在验证登录状态...")
            await scraper.page.goto("https://weibo.com")
            await scraper.page.wait_for_timeout(3000)
            
            # 检查是否有登录按钮
            login_btn = await scraper.page.query_selector('text=/登录|Login/')
            if login_btn:
                print("[WARN] 登录状态已失效，需要重新登录")
                has_login = False
            else:
                print("[OK] 登录状态有效")
        
        if not has_login:
            # 登录流程
            await scraper.login()
        
        # 提取链接
        links = await scraper.extract_links()
        if not links:
            print("[WARN] 没有找到链接")
            return
        
        # 抓取
        await scraper.scrape_all(links)
        
        # 保存
        if scraper.qa_data:
            files = await scraper.save()
            print("\n" + "=" * 60)
            print(" [OK] 全部完成！")
            print("=" * 60)
            for f in files:
                print(f"  {f}")
        
        print("\n>>> 按回车键关闭浏览器 <<<")
        input()
        
    except Exception as e:
        print(f"\n[ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键关闭...")
    finally:
        await scraper.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n程序出错: {e}")
        import traceback
        traceback.print_exc()
        print("\n" + "=" * 60)
        input("按回车键退出...")
