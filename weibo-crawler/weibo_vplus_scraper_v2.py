#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微博 V+ 问答抓取脚本 - 优化版
改进点：
1. 使用 storage_state 保存完整登录状态，避免每次扫码
2. 优化内容提取逻辑，精确获取问答内容
3. 完善"免费围观"按钮处理
4. 增加更多调试信息和重试机制
"""

import asyncio
import json
import os
import time
import re
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# 配置
TARGET_UID = "1039916297"  # 二总 UID
LIST_URL = f"https://weibo.com/{TARGET_UID}?tabtype=article"
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 存储状态文件
STORAGE_STATE_FILE = OUTPUT_DIR / "weibo_storage_state.json"
COOKIES_FILE = OUTPUT_DIR / "weibo_cookies.json"


class WeiboVPlusScraper:
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.qa_data = []
        
    async def start(self):
        print("=" * 60)
        print("微博 V+ 问答抓取工具 v2.0")
        print("=" * 60)
        print()
        
        self.playwright = await async_playwright().start()
        
        self.browser = await self.playwright.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        
        # 尝试加载存储状态
        storage_state = None
        if STORAGE_STATE_FILE.exists():
            try:
                with open(STORAGE_STATE_FILE, 'r', encoding='utf-8') as f:
                    storage_state = json.load(f)
                print("[✓] 已加载保存的登录状态")
            except Exception as e:
                print(f"[!] 加载存储状态失败: {e}")
        
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 900},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0',
            storage_state=storage_state
        )
        
        self.page = await self.context.new_page()
        
        # 额外加载 cookies（兼容旧版本）
        if COOKIES_FILE.exists() and not storage_state:
            try:
                with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                await self.context.add_cookies(cookies)
                print("[✓] 已加载 cookies")
            except Exception as e:
                print(f"[!] 加载 cookies 失败: {e}")
        
        return storage_state is not None or COOKIES_FILE.exists()
    
    async def save_storage_state(self):
        """保存完整的存储状态 - 包含 cookies 和 localStorage"""
        try:
            storage_state = await self.context.storage_state()
            with open(STORAGE_STATE_FILE, 'w', encoding='utf-8') as f:
                json.dump(storage_state, f, ensure_ascii=False, indent=2)
            print("[✓] 登录状态已保存（包含 cookies 和 localStorage）")
            
            # 同时单独保存 cookies 以便调试
            cookies = await self.context.cookies()
            with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"[!] 保存登录状态失败: {e}")
    
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
            # 等待登录成功（URL变化）
            await self.page.wait_for_url(lambda url: "weibo.com/login" not in url and "weibo.com" in url, timeout=60000)
            print("[✓] 登录成功！")
            
            # 保存存储状态
            await self.save_storage_state()
            
            # 同时保存 cookies 兼容旧版本
            cookies = await self.context.cookies()
            with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, ensure_ascii=False, indent=2)
            
            # 额外等待一下确保状态稳定
            await self.page.wait_for_timeout(3000)
            
            return True
            
        except Exception as e:
            print(f"[✗] 登录超时或失败: {e}")
            return False
    
    async def check_login_status(self):
        """检查是否仍然登录 - 通过访问个人页面验证"""
        try:
            # 访问目标用户页面验证登录
            await self.page.goto(LIST_URL)
            await self.page.wait_for_timeout(5000)
            
            # 检查是否有登录提示
            login_prompt = await self.page.query_selector('text=/登录.*查看|请先登录/')
            if login_prompt:
                print("[!] 检测到登录提示，登录状态已失效")
                return False
            
            # 检查页面是否有用户相关内容
            page_content = await self.page.content()
            
            # 检查是否有文章列表（登录后应该能看到）
            has_content = await self.page.evaluate('''() => {
                const articles = document.querySelectorAll('article, [class*="article"], [class*="card"]');
                return articles.length > 0;
            }''')
            
            if has_content:
                print("[✓] 登录状态有效，已加载内容")
                return True
            
            # 检查是否有登录按钮
            login_btn = await self.page.query_selector('text=/登录|Login/')
            if login_btn:
                print("[!] 发现登录按钮，登录状态已失效")
                return False
            
            print("[?] 登录状态不确定，将尝试继续")
            return True
        except Exception as e:
            print(f"[!] 检查登录状态出错: {e}")
            return False
    
    async def get_qa_links_from_list(self):
        print("\n" + "=" * 60)
        print("正在获取问答列表...")
        print("=" * 60)
        
        await self.page.goto(LIST_URL)
        print(f"当前页面: {self.page.url}")
        print("等待页面加载...")
        
        # 等待更长时间让页面完全加载
        await self.page.wait_for_timeout(8000)
        
        # 滚动加载更多内容
        print("正在滚动加载更多内容...")
        for i in range(5):
            await self.page.evaluate("window.scrollBy(0, 800)")
            await self.page.wait_for_timeout(1500)
        
        # 保存截图看看页面
        screenshot_path = OUTPUT_DIR / "debug_list_page.png"
        await self.page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"[✓] 已保存页面截图: {screenshot_path}")
        
        # 获取所有文章/问答链接
        qa_links = []
        
        # 方法1: 通过文章卡片获取
        article_links = await self.page.query_selector_all('a[href*="/ttarticle/p/show"]')
        print(f"找到 {len(article_links)} 个文章链接（方法1）")
        
        for link in article_links:
            try:
                href = await link.get_attribute('href')
                if href:
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif href.startswith('/'):
                        href = 'https://weibo.com' + href
                    if href not in qa_links:
                        qa_links.append(href)
            except:
                continue
        
        # 方法2: 通过特定选择器获取
        try:
            # 尝试获取文章列表中的链接
            card_links = await self.page.evaluate('''() => {
                const links = [];
                const cards = document.querySelectorAll('[class*="card"], [class*="article"], [class*="list"]');
                cards.forEach(card => {
                    const a = card.querySelector('a[href*="article"]') || card.querySelector('a[href*="/p/"]');
                    if (a && a.href) links.push(a.href);
                });
                return links;
            }''')
            for href in card_links:
                if href and href not in qa_links:
                    qa_links.append(href)
            print(f"找到 {len(card_links)} 个链接（方法2）")
        except Exception as e:
            print(f"方法2出错: {e}")
        
        print(f"\n[✓] 共找到 {len(qa_links)} 个文章/问答链接")
        
        # 显示前10个
        if qa_links:
            print("\n前10个链接:")
            for i, link in enumerate(qa_links[:10], 1):
                print(f"  {i}. {link}")
        
        return qa_links
    
    async def click_free_view_button(self):
        """尝试点击免费围观按钮，并取消分享到微博的勾选"""
        btn_patterns = [
            'text=免费围观',
            'text=免费观看', 
            'text=围观',
            'button:has-text("免费")',
            'a:has-text("免费")',
            '[class*="btn"]:has-text("免费")',
            '[class*="button"]:has-text("免费")',
        ]
        
        for pattern in btn_patterns:
            try:
                btn = await self.page.query_selector(pattern)
                if btn:
                    print(f"  发现按钮: {pattern}")
                    
                    # 先找勾选框并取消勾选 - 使用多种选择器
                    checkbox_selectors = [
                        'input[type="checkbox"]',
                        '.woo-checkbox-input',
                        '[class*="checkbox"] input',
                        'input[name*="share"]',
                        'input[id*="share"]'
                    ]
                    
                    for checkbox_sel in checkbox_selectors:
                        try:
                            checkbox = await self.page.query_selector(checkbox_sel)
                            if checkbox:
                                is_checked = await checkbox.is_checked()
                                if is_checked:
                                    await checkbox.click()
                                    print("  [✓] 已取消勾选'分享到微博'")
                                    await self.page.wait_for_timeout(800)
                                else:
                                    print("  [i] 勾选框未选中，无需取消")
                                break
                        except Exception as ce:
                            continue
                    
                    # 通过文本找"分享"相关的label并点击
                    try:
                        share_label = await self.page.query_selector('text=/分享到|分享/')
                        if share_label:
                            # 找相邻的checkbox
                            checkbox = await share_label.evaluate_handle('el => el.previousElementSibling || el.querySelector("input")')
                            if checkbox:
                                is_checked = await checkbox.is_checked()
                                if is_checked:
                                    await share_label.click()
                                    print("  [✓] 已通过label取消勾选分享")
                                    await self.page.wait_for_timeout(800)
                    except:
                        pass
                    
                    # 点击按钮
                    await btn.click()
                    print(f"  [✓] 已点击'免费围观'按钮")
                    await self.page.wait_for_timeout(4000)
                    return True
            except Exception as e:
                continue
        
        return False
    
    async def extract_qa_content(self):
        """提取问答内容 - 针对V+问答页面优化"""
        content = {
            'question': '',
            'answer': '',
            'title': '',
            'time': ''
        }
        
        try:
            # 获取页面标题
            content['title'] = await self.page.title()
            
            # 等待内容加载 - V+内容可能需要更长时间
            await self.page.wait_for_timeout(4000)
            
            # 专门针对微博V+问答页面的提取策略
            vplus_content = await self.page.evaluate('''() => {
                const result = {
                    question: '',
                    answer: '',
                    time: ''
                };
                
                // V+问答通常的结构：
                // 1. 问题在标题或特定区域
                // 2. 答案在正文区域
                
                // 尝试获取标题作为问题
                const titleSelectors = [
                    'h1[class*="title"]',
                    'h2[class*="title"]',
                    '.article-title',
                    '[class*="article"] h1',
                    '[class*="detail"] h1',
                    '[class*="content"] h1'
                ];
                
                for (let sel of titleSelectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        result.question = el.innerText.trim();
                        break;
                    }
                }
                
                // 尝试获取答案内容
                const answerSelectors = [
                    '.article-content',
                    '[class*="article-body"]',
                    '[class*="content-detail"]',
                    'article .content',
                    '.WB_detail',
                    '[class*="detail-content"]'
                ];
                
                for (let sel of answerSelectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        result.answer = el.innerText.trim();
                        break;
                    }
                }
                
                // 如果上面的没找到，尝试从段落组合
                if (!result.answer) {
                    const paragraphs = document.querySelectorAll('article p, .content p, [class*="article"] p');
                    const texts = [];
                    paragraphs.forEach(p => {
                        const text = p.innerText.trim();
                        if (text.length > 10) {
                            texts.push(text);
                        }
                    });
                    if (texts.length > 0) {
                        result.answer = texts.join('\\n\\n');
                    }
                }
                
                // 获取发布时间
                const timeSelectors = [
                    'time',
                    '[class*="time"]',
                    '[class*="date"]',
                    '[class*="publish"]'
                ];
                
                for (let sel of timeSelectors) {
                    const el = document.querySelector(sel);
                    if (el) {
                        result.time = el.innerText.trim();
                        break;
                    }
                }
                
                return result;
            }''')
            
            if vplus_content:
                content['question'] = vplus_content.get('question', '')
                content['answer'] = vplus_content.get('answer', '')
                content['time'] = vplus_content.get('time', '')
            
            # 备用方案：获取页面所有文本
            if not content['answer']:
                all_text = await self.page.evaluate('''() => {
                    // 移除无关元素
                    const toRemove = document.querySelectorAll('script, style, nav, header, footer, aside');
                    toRemove.forEach(el => el.remove());
                    
                    // 尝试找主要内容区域
                    const main = document.querySelector('main, article, [class*="main"], [class*="content"]') 
                                || document.body;
                    return main.innerText;
                }''')
                
                if all_text:
                    # 尝试分离问题和答案
                    lines = [l.strip() for l in all_text.split('\n') if l.strip()]
                    if lines and not content['question']:
                        content['question'] = lines[0][:200]
                    content['answer'] = all_text[:8000]
            
            # 提取时间（正则匹配）
            if not content['time']:
                page_text = await self.page.evaluate('() => document.body.innerText')
                time_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', page_text)
                if time_match:
                    content['time'] = time_match.group(1)
            
            return content
            
        except Exception as e:
            print(f"  [!] 提取内容出错: {e}")
            import traceback
            traceback.print_exc()
            return content
    
    async def scrape_single_qa(self, url, index, total):
        print(f"\n[{index}/{total}] 处理: {url}")
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                await self.page.goto(url)
                await self.page.wait_for_timeout(4000)
                
                # 获取页面标题
                title = await self.page.title()
                print(f"  页面标题: {title}")
                
                # 检查是否需要登录
                if "登录" in title or "login" in title.lower():
                    print("  [!] 需要登录，跳过此页面")
                    return {
                        'index': index,
                        'url': url,
                        'error': '需要登录',
                        'crawled_at': datetime.now().isoformat()
                    }
                
                # 保存调试截图
                if index <= 3:  # 只保存前3个的截图
                    debug_path = OUTPUT_DIR / f"debug_qa_{index}.png"
                    await self.page.screenshot(path=str(debug_path), full_page=True)
                
                # 尝试点击"免费围观"按钮
                btn_clicked = await self.click_free_view_button()
                if not btn_clicked:
                    print("  [i] 无需点击按钮或按钮已处理")
                
                # 等待内容加载
                await self.page.wait_for_timeout(3000)
                
                # 提取内容
                content = await self.extract_qa_content()
                
                # 构建结果
                qa_item = {
                    'index': index,
                    'url': url,
                    'title': content.get('title', title),
                    'question': content.get('question', ''),
                    'answer': content.get('answer', ''),
                    'publish_time': content.get('time', ''),
                    'crawled_at': datetime.now().isoformat()
                }
                
                content_len = len(qa_item['question']) + len(qa_item['answer'])
                print(f"  [✓] 抓取成功，内容长度: {content_len}")
                
                if content_len < 50:
                    print(f"  [!] 警告: 内容可能不完整")
                
                return qa_item
                
            except Exception as e:
                print(f"  [✗] 尝试 {attempt + 1}/{max_retries} 失败: {e}")
                if attempt < max_retries - 1:
                    await self.page.wait_for_timeout(3000)
                else:
                    return {
                        'index': index,
                        'url': url,
                        'error': str(e),
                        'crawled_at': datetime.now().isoformat()
                    }
    
    async def scrape_all_qa(self, qa_links, limit=None):
        print("\n" + "=" * 60)
        print("开始逐个抓取")
        print("=" * 60)
        
        total = len(qa_links)
        if limit:
            print(f"本次只抓前 {limit} 个\n")
            target_count = min(limit, total)
        else:
            print(f"共 {total} 个链接\n")
            target_count = total
        
        for i, url in enumerate(qa_links[:target_count], 1):
            qa_item = await self.scrape_single_qa(url, i, target_count)
            if qa_item:
                self.qa_data.append(qa_item)
            
            # 随机延迟，避免被封
            delay = 2 + (i % 3)
            await asyncio.sleep(delay)
        
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
        print(f"[✓] JSON: {json_file}")
        
        # 保存为 Markdown（更适合阅读）
        md_file = OUTPUT_DIR / f"erzong_qa_{timestamp}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# 二总 V+ 问答\n\n")
            f.write(f"抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"数量: {len(qa_items)}\n\n")
            f.write("---\n\n")
            
            for item in qa_items:
                f.write(f"## 【{item['index']}】{item['title']}\n\n")
                f.write(f"**链接**: {item['url']}\n\n")
                if item.get('publish_time'):
                    f.write(f"**发布时间**: {item['publish_time']}\n\n")
                
                if 'error' in item:
                    f.write(f"> ⚠️ 错误: {item['error']}\n\n")
                else:
                    if item.get('question'):
                        f.write(f"### 问题\n\n{item['question']}\n\n")
                    if item.get('answer'):
                        f.write(f"### 回答\n\n{item['answer']}\n\n")
                
                f.write("---\n\n")
        
        print(f"[✓] Markdown: {md_file}")
        
        # 同时保存为文本（兼容旧格式）
        txt_file = OUTPUT_DIR / f"erzong_qa_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"二总 V+ 问答\n")
            f.write(f"抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"数量: {len(qa_items)}\n")
            f.write("=" * 60 + "\n\n")
            
            for item in qa_items:
                f.write(f"【{item['index']}】{item['title']}\n")
                f.write(f"URL: {item['url']}\n")
                if item.get('publish_time'):
                    f.write(f"时间: {item['publish_time']}\n")
                if 'error' in item:
                    f.write(f"错误: {item['error']}\n")
                else:
                    if item.get('question'):
                        f.write(f"\n[问题]\n{item['question']}\n")
                    if item.get('answer'):
                        f.write(f"\n[回答]\n{item['answer']}\n")
                f.write("\n" + "=" * 60 + "\n\n")
        
        print(f"[✓] TXT: {txt_file}")
        
        return json_file, md_file, txt_file
    
    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


async def main():
    scraper = WeiboVPlusScraper()
    
    try:
        logged_in = await scraper.start()
        
        # 检查登录状态
        if logged_in:
            is_valid = await scraper.check_login_status()
            if not is_valid:
                logged_in = False
        
        if not logged_in:
            login_success = await scraper.login_with_qr()
            if not login_success:
                print("[✗] 登录失败，退出")
                return
        
        # 获取问答链接
        qa_links = await scraper.get_qa_links_from_list()
        
        if not qa_links:
            print("\n[!] 未找到任何链接，请检查截图")
            input("\n按回车键关闭...")
            return
        
        print(f"\n[✓] 找到 {len(qa_links)} 个链接")
        
        # 询问抓取数量
        print("\n选择抓取数量:")
        print("  1. 测试模式 - 抓取前3个")
        print("  2. 标准模式 - 抓取前10个")
        print("  3. 全部抓取 - 抓取所有链接")
        print("  4. 自定义数量")
        
        # 非交互模式默认选2
        choice = "2"
        limit = 10
        
        if choice == "1":
            limit = 3
        elif choice == "2":
            limit = 10
        elif choice == "3":
            limit = None
        elif choice == "4":
            limit = 5  # 默认
        
        print(f"\n将抓取 {limit if limit else len(qa_links)} 个问答...")
        await asyncio.sleep(1)
        
        # 抓取
        qa_items = await scraper.scrape_all_qa(qa_links, limit=limit)
        
        # 保存
        if qa_items:
            files = await scraper.save_data(qa_items)
            print("\n" + "=" * 60)
            print("[✓] 完成！")
            print("=" * 60)
            for f in files:
                print(f"  {f}")
        
        input("\n按回车键关闭浏览器...")
        
    except Exception as e:
        print(f"\n[✗] 错误: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键关闭...")
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
