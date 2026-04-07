#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
二总 V+ 问答抓取脚本 - v4.0
改进点：
1. 同步 Playwright，更稳定
2. 更精准的内容提取逻辑
3. 保持手动控制（需用户手动围观解锁）
4. 输出格式：只保留问题和回答
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

SCRIPT_DIR = Path(__file__).parent.resolve()
STORAGE_STATE_FILE = SCRIPT_DIR / "output" / "weibo_storage_state.json"
OUTPUT_DIR = SCRIPT_DIR / "output" / "vplus"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ERZONG_UID = "1039916297"
ARTICLE_LIST_URL = f"https://weibo.com/{ERZONG_UID}?tabtype=article"


def clean_text(text: str) -> str:
    """清理文本中的多余空行和特殊符号"""
    if not text:
        return ""
    text = re.sub(r'\r\n|\r|\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def extract_qa_from_page(page) -> dict:
    """
    从页面中提取问题和回答。
    尝试多种选择器，适配微博 V+ 文章的不同结构。
    """
    return page.evaluate("""() => {
        const result = { question: '', answer: '' };
        
        // 1. 尝试 V+ 问答专用结构
        const qEl = document.querySelector('.question-text, [class*="question"] h3, .qa-question, .vplus-question');
        const aEl = document.querySelector('.answer-text, [class*="answer"] .content, .qa-answer, .vplus-answer');
        if (qEl && aEl) {
            result.question = qEl.innerText.trim();
            result.answer = aEl.innerText.trim();
            return result;
        }
        
        // 2. 尝试从 h1 获取问题，从 article-content 获取回答
        const h1 = document.querySelector('h1');
        const article = document.querySelector('.article-content, .article-body, article, [class*="article_body"]');
        if (h1 && article) {
            result.question = h1.innerText.trim();
            result.answer = article.innerText.trim();
            return result;
        }
        
        // 3. 尝试微博通用的 WB_detail / content
        const wbDetail = document.querySelector('.WB_detail, .wbpro-feed-content');
        if (wbDetail) {
            const texts = [];
            wbDetail.querySelectorAll('p, div').forEach(p => {
                const t = p.innerText.trim();
                if (t.length > 5) texts.push(t);
            });
            if (texts.length > 1) {
                result.question = texts[0];
                result.answer = texts.slice(1).join('\\n\\n');
            } else if (texts.length === 1) {
                result.answer = texts[0];
            }
            return result;
        }
        
        // 4. Fallback: 找页面中最大的文本块
        let maxLen = 0;
        let best = null;
        document.querySelectorAll('div, section').forEach(el => {
            const t = el.innerText.trim();
            if (t.length > maxLen && t.length < 10000) {
                maxLen = t.length;
                best = el;
            }
        });
        if (best) {
            const allText = best.innerText.trim();
            const lines = allText.split('\\n').filter(l => l.trim().length > 0);
            if (lines.length > 1) {
                result.question = lines[0];
                result.answer = lines.slice(1).join('\\n\\n');
            } else {
                result.answer = allText;
            }
        }
        
        return result;
    }""")


def main():
    print("=" * 60)
    print(" 二总 V+ 问答抓取工具 v4.0 ")
    print("=" * 60)
    print()

    if not STORAGE_STATE_FILE.exists():
        print(f"[ERROR] 未找到登录状态文件: {STORAGE_STATE_FILE}")
        print("请先运行之前的微博登录脚本生成 storage_state。")
        input("按回车键退出...")
        return

    qa_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled'])
        context = browser.new_context(
            viewport={'width': 1280, 'height': 900},
            storage_state=str(STORAGE_STATE_FILE)
        )
        page = context.new_page()

        # 进入文章列表页
        print(f"[1/4] 正在打开二总文章列表页...")
        page.goto(ARTICLE_LIST_URL, timeout=30000)
        page.wait_for_timeout(3000)

        # 检查是否需要重新登录
        if page.locator('text=登录').count() > 0 and page.locator('text=注册').count() > 0:
            print("[WARN] 登录状态已过期，请在浏览器中扫码登录...")
            input("登录完成后，按回车键继续...")
            context.storage_state(path=str(STORAGE_STATE_FILE))
            print("[OK] 已更新登录状态")

        print(f"\n[2/4] 请手动操作：")
        print("  1. 在浏览器中向下滚动，加载更多 V+ 问答文章")
        print("  2. 确认想抓取的问答都已显示在列表中")
        print(f"  当前页面: {ARTICLE_LIST_URL}")
        input("\n>>> 完成后按回车键继续...")

        # 等待页面稳定
        page.wait_for_timeout(2000)

        # 提取文章链接（兼容新旧版微博结构）
        print("\n[3/4] 正在提取问答链接...")
        
        # 先尝试提取带 V+ 标识的卡片
        links = page.evaluate("""() => {
            const result = [];
            const seen = new Set();
            
            // 策略1: 找包含 "V+" 字样的卡片/feed
            document.querySelectorAll('*').forEach(el => {
                const text = el.innerText || '';
                if (text.includes('V+') || text.includes('付费') || text.includes('围观')) {
                    const card = el.closest('.wbpro-feed-content, [class*="card"], [class*="feed"], article, [class*="vue-recycle-scroller__item-view"]');
                    if (card) {
                        const a = card.querySelector('a[href*="/status/"], a[href*="/ttarticle"], a[href*="weibo.com"]');
                        if (a) {
                            const url = a.href;
                            // 找标题: 先找 h3/h4, 再找最长的文本段落
                            let title = '';
                            const titleEl = card.querySelector('h3, h4, [class*="title"]');
                            if (titleEl) {
                                title = titleEl.innerText.trim();
                            } else {
                                let best = '';
                                card.querySelectorAll('span, p, div').forEach(t => {
                                    const txt = t.innerText.trim();
                                    if (txt.length > best.length && txt.length < 200 && !txt.includes('转发') && !txt.includes('评论') && !txt.includes('赞')) {
                                        best = txt;
                                    }
                                });
                                title = best;
                            }
                            
                            if (url && !seen.has(url) && title && title.length > 5 && title.length < 300) {
                                if (!url.includes('/home') && !url.includes('/search') && !url.includes('/login') && !url.includes('/u/')) {
                                    seen.add(url);
                                    result.push({ url, title });
                                }
                            }
                        }
                    }
                }
            });
            
            // 策略2: 如果没找到，用传统选择器兜底
            if (result.length === 0) {
                const selectors = [
                    'a[href*="/ttarticle/p/show"]',
                    'a[href*="/status/"]',
                ];
                for (const sel of selectors) {
                    document.querySelectorAll(sel).forEach(a => {
                        const url = a.href;
                        let title = a.innerText.trim();
                        if (!title || title.length < 5) {
                            let parent = a.closest('.wbpro-feed-content, [class*="card"], [class*="feed"], article');
                            if (parent) {
                                const titleEl = parent.querySelector('h3, h4, [class*="title"], [class*="text"]');
                                if (titleEl) title = titleEl.innerText.trim();
                            }
                        }
                        if (url && !seen.has(url) && title && title.length > 5 && title.length < 300) {
                            if (!url.includes('/home') && !url.includes('/search') && !url.includes('/login') && !url.includes('/u/')) {
                                seen.add(url);
                                result.push({ url, title });
                            }
                        }
                    });
                }
            }
            
            return result;
        }""")

        print(f"[OK] 找到 {len(links)} 个文章链接")
        
        # 如果 article tab 没找到，切到主页 feed 试试
        if not links:
            print("[INFO] article 列表页未找到链接，尝试切到主页 feed 查找 V+ 动态...")
            page.goto(f"https://weibo.com/{ERZONG_UID}", timeout=30000)
            page.wait_for_timeout(4000)
            
            print("\n请在浏览器中向下滚动主页，加载更多 V+ 微博动态...")
            input(">>> 完成后按回车键继续...")
            page.wait_for_timeout(2000)
            
            links = page.evaluate("""() => {
                const result = [];
                const seen = new Set();
                document.querySelectorAll('*').forEach(el => {
                    const text = el.innerText || '';
                    if (text.includes('V+') || text.includes('付费') || text.includes('围观')) {
                        const card = el.closest('.wbpro-feed-content, [class*="card"], [class*="feed"], [class*="vue-recycle-scroller__item-view"]');
                        if (card) {
                            const a = card.querySelector('a[href*="/status/"]');
                            if (a) {
                                const url = a.href;
                                let title = '';
                                const titleEl = card.querySelector('h3, h4, [class*="title"]');
                                if (titleEl) {
                                    title = titleEl.innerText.trim();
                                } else {
                                    let best = '';
                                    card.querySelectorAll('span, p, div').forEach(t => {
                                        const txt = t.innerText.trim();
                                        if (txt.length > best.length && txt.length < 200 && !txt.includes('转发') && !txt.includes('评论') && !txt.includes('赞')) {
                                            best = txt;
                                        }
                                    });
                                    title = best;
                                }
                                if (url && !seen.has(url) && title && title.length > 5) {
                                    seen.add(url);
                                    result.push({ url, title });
                                }
                            }
                        }
                    }
                });
                return result;
            }""")
            
            print(f"[OK] 主页 feed 找到 {len(links)} 个 V+ 动态链接")
        
        if not links:
            print("[WARN] 未找到任何 V+ 问答链接。可能原因：")
            print("  1. 页面未滚动加载足够内容")
            print("  2. 微博结构已更新，需要调整选择器")
            print("  3. 二总近期没有发布 V+ 问答")
            input("按回车键退出...")
            browser.close()
            return

        # 显示并确认
        print("\n前5个链接预览:")
        for i, link in enumerate(links[:5], 1):
            print(f"  {i}. {link['title'][:50]}")
        if len(links) > 5:
            print(f"  ... 还有 {len(links) - 5} 个")

        confirm = input(f"\n确认要抓取这 {len(links)} 篇文章吗？ (回车=确认 / n=取消): ").strip().lower()
        if confirm == 'n':
            print("已取消")
            browser.close()
            return

        # 逐个抓取
        print("\n[4/4] 开始抓取问答内容...")
        print("-" * 60)

        for i, link in enumerate(links, 1):
            url = link['url']
            title = link['title']
            print(f"\n[{i}/{len(links)}] {title[:40]}")
            print(f"      {url[:70]}...")

            new_page = context.new_page()
            try:
                new_page.goto(url, timeout=30000)
                new_page.wait_for_timeout(2500)

                content = new_page.content()
                need_unlock = '免费围观' in content or '围观' in content or '解锁' in content or '付费' in content

                if need_unlock:
                    print("      [⚠️] 该问答需要解锁（V+ 内容）")
                    print("      >>> 请执行以下操作：")
                    print("          1. 在手机微博 APP 或当前浏览器中点击\"免费围观\"")
                    print("          2. 支付 1 元解锁后，等待答案显示")
                    print("          3. 回到这里按回车键继续")
                    input()
                    new_page.reload(timeout=30000)
                    new_page.wait_for_timeout(2500)

                # 提取内容
                data = extract_qa_from_page(new_page)
                question = clean_text(data.get('question', ''))
                answer = clean_text(data.get('answer', ''))

                # 如果没提取到问题，用标题兜底
                if not question and title:
                    question = title

                # 清理回答中的元数据行
                answer_lines = []
                skip_patterns = ['提问者', '围观人数', '问题价值', '付费阅读', ' V+ ', '阅读全文']
                for line in answer.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    if any(p in line for p in skip_patterns):
                        continue
                    answer_lines.append(line)
                answer = '\n\n'.join(answer_lines)

                if answer and len(answer) > 20:
                    print(f"      [OK] 提取成功，回答长度 {len(answer)} 字")
                    qa_data.append({
                        'index': i,
                        'url': url,
                        'question': question,
                        'answer': answer,
                        'crawled_at': datetime.now().isoformat()
                    })
                else:
                    print(f"      [WARN] 内容为空或太短，可能未正确解锁")
                    qa_data.append({
                        'index': i,
                        'url': url,
                        'question': question,
                        'answer': '[抓取失败：内容为空，请检查是否已解锁]',
                        'crawled_at': datetime.now().isoformat()
                    })

            except Exception as e:
                print(f"      [ERROR] {e}")
                qa_data.append({
                    'index': i,
                    'url': url,
                    'question': title,
                    'answer': f'[抓取失败: {e}]',
                    'crawled_at': datetime.now().isoformat()
                })
            finally:
                new_page.close()

        browser.close()

    # 保存
    if qa_data:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON
        json_file = OUTPUT_DIR / f"erzong_qa_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(qa_data, f, ensure_ascii=False, indent=2)

        # Markdown - 只保留问题和回答
        md_file = OUTPUT_DIR / f"erzong_qa_{timestamp}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# 二总 V+ 问答\n\n")
            f.write(f"抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"数量: {len(qa_data)}\n\n---\n\n")

            for item in qa_data:
                f.write(f"## 问答 #{item['index']}\n\n")
                f.write(f"**问题**：{item.get('question', '无标题')}\n\n")
                f.write(f"**回答**：{item.get('answer', '')}\n\n")
                f.write("---\n\n")

        print("\n" + "=" * 60)
        print(" [OK] 全部完成！")
        print("=" * 60)
        print(f"  JSON:  {json_file}")
        print(f"  Markdown: {md_file}")

    input("\n按回车键退出...")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[ERROR] 程序异常: {e}")
        import traceback
        traceback.print_exc()
        input("\n按回车键退出...")
