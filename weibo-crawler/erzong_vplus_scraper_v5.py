#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
二总 V+ 问答抓取器 v5
基于本地 Playwright (sync API)，稳定、可断点续传。
支持两种模式：
  1) 自动尝试抓取文章列表（可能因微博改版失效）
  2) 读取用户提供的 links.txt 精准批量提取（推荐）

用法：
  1. 先登录：python erzong_vplus_scraper_v5.py --login
  2. 模式A全自动：python erzong_vplus_scraper_v5.py --auto-collect
  3. 模式B半自动：把链接写入 links.txt，然后 python erzong_vplus_scraper_v5.py

输出：output/erzong_v5/{日期}/ 下，每个问答一个 .md + 汇总 qa.jsonl
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright, Page

# ==================== 配置 ====================
ERZONG_UID = "1039916297"
STORAGE_STATE = Path("weibo_crawler/output/weibo_storage_state.json")
OUTPUT_BASE = Path("weibo_crawler/output/erzong_v5")
LINKS_FILE = Path("weibo_crawler/links.txt")
VISITED_FILE = OUTPUT_BASE / "visited.json"
# ==============================================


def ensure_output_dir() -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    out = OUTPUT_BASE / today
    out.mkdir(parents=True, exist_ok=True)
    return out


def load_visited() -> set:
    if VISITED_FILE.exists():
        with open(VISITED_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_visited(visited: set):
    OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
    with open(VISITED_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(visited)), f, ensure_ascii=False, indent=2)


def sanitize_filename(text: str, max_len: 40) -> str:
    text = text.strip().replace("\n", " ")
    text = re.sub(r'[\\/:*?"<>|]', "", text)
    if len(text) > max_len:
        text = text[:max_len]
    return text or "untitled"


# ==================== 浏览器启动 ====================
def launch_browser(headless: bool = False):
    p = sync_playwright().start()
    browser = p.chromium.launch(
        headless=headless,
        slow_mo=80,
        args=["--disable-blink-features=AutomationControlled"],
    )
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    )
    if STORAGE_STATE.exists():
        context = browser.new_context(
            storage_state=str(STORAGE_STATE),
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        print(f"[INFO] 已加载登录态: {STORAGE_STATE}")
    page = context.new_page()
    return p, browser, context, page


# ==================== 登录 & 保存状态 ====================
def do_login():
    print("=" * 50)
    print("微博登录助手")
    print("=" * 50)
    p, browser, context, page = launch_browser(headless=False)

    print("[STEP 1] 打开微博登录页...")
    page.goto("https://weibo.com/login", wait_until="domcontentloaded")
    print("[STEP 2] 请手动完成扫码/密码登录")
    print("[STEP 3] 登录成功后，按回车保存状态...")
    input(">>> 登录完成并按回车继续: ")

    STORAGE_STATE.parent.mkdir(parents=True, exist_ok=True)
    context.storage_state(path=str(STORAGE_STATE))
    print(f"[OK] 登录态已保存到: {STORAGE_STATE}")

    # 顺手验证一下二总页面能否访问
    print("[STEP 4] 验证二总主页访问...")
    page.goto(f"https://weibo.com/u/{ERZONG_UID}", wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    if page.locator("text=文章").count() > 0 or page.locator('a[href*="article"]').count() > 0:
        print("[OK] 已确认能看到'文章'标签，准备就绪。")
    else:
        print("[WARN] 未检测到'文章'标签，可能是加载慢或页面结构有变。")

    browser.close()
    p.stop()


# ==================== 自动收集链接（尝试） ====================
def auto_collect_links(page: Page) -> list:
    print("[MODE] 自动收集文章链接...")
    page.goto(f"https://weibo.com/u/{ERZONG_UID}?tabtype=article", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # 尝试点击"文章"标签（如果 tabtype=article 没自动切过去）
    try:
        article_tab = page.locator('a[href*="tabtype=article"]').first
        if article_tab.count() > 0:
            article_tab.click()
            page.wait_for_timeout(2500)
            print("[INFO] 已点击'文章'标签")
    except Exception:
        pass

    links = set()
    last_count = 0
    stagnant = 0
    max_scrolls = 30

    print("[INFO] 开始滚动加载文章列表...")
    for i in range(max_scrolls):
        # 抓真正的 V+ 问答链接
        hrefs = page.eval_on_selector_all(
            'a[href*="ttwenda/p/show?id="]',
            "els => els.map(e => e.href)"
        )
        for h in hrefs:
            if "weibo.com" in h and "publisher3in1" not in h:
                # 保留 id 参数，只去掉追踪参数
                if "?" in h:
                    base, query = h.split("?", 1)
                    params = [p for p in query.split("&") if p.startswith("id=")]
                    clean = base + "?" + "&".join(params) if params else base
                else:
                    clean = h
                links.add(clean)

        # 兜底：抓所有 a 标签，过滤出 ttwenda 特征
        if len(links) == 0:
            all_hrefs = page.eval_on_selector_all(
                "a",
                "els => els.map(e => e.href).filter(h => h && h.includes('weibo.com') && h.includes('ttwenda/p/show?id='))"
            )
            for h in all_hrefs:
                if "publisher3in1" not in h:
                    if "?" in h:
                        base, query = h.split("?", 1)
                        params = [p for p in query.split("&") if p.startswith("id=")]
                        clean = base + "?" + "&".join(params) if params else base
                    else:
                        clean = h
                    links.add(clean)

        if len(links) > last_count:
            last_count = len(links)
            stagnant = 0
            print(f"  滚动 {i+1}: 已收集 {len(links)} 个链接")
        else:
            stagnant += 1
            if stagnant >= 3:
                print("[INFO] 连续3次无新增，停止滚动")
                break

        page.evaluate("window.scrollBy(0, 1200)")
        page.wait_for_timeout(1800)

    result = sorted(list(links))
    if len(result) == 0:
        print("[WARN] 自动收集未抓到任何链接。请改用模式B：把链接写入 links.txt 后再运行。")
    else:
        # 自动保存一份备用
        LINKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LINKS_FILE, "w", encoding="utf-8") as f:
            for u in result:
                f.write(u + "\n")
        print(f"[OK] 已保存 {len(result)} 个链接到 {LINKS_FILE}")
    return result


# ==================== 处理单个问答 ====================
def process_single_qa(page: Page, url: str, idx: int, total: int, out_dir: Path) -> dict:
    print(f"\n[{idx}/{total}] 打开: {url}")
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)

    # --- 校验：如果页面被重定向到非问答页，直接跳过 ---
    current_url = page.url
    if "ttwenda/p/show" not in current_url:
        print(f"  [SKIP] 链接失效/重定向到: {current_url[:80]}")
        return {}

    # --- 检测是否需要免费围观 ---
    need_unlock = page.locator("text=免费围观").count() > 0
    if need_unlock:
        print("  [LOCK] 检测到未解锁，执行免费围观...")
        # 找到"免费围观"按钮附近的 checkbox
        checkbox = page.locator('input[type="checkbox"]').filter(has=page.locator("xpath=..")).filter(
            has=page.locator("text=分享到微博")
        ).first
        if checkbox.count() == 0:
            # 兜底：找按钮前面的 checkbox
            checkbox = page.locator("text=免费围观").first.locator("xpath=../../preceding-sibling::*//input[@type='checkbox']")
        if checkbox.count() > 0:
            if checkbox.is_checked():
                checkbox.click()
                print("  [OK] 已取消'分享到微博'勾选")
                page.wait_for_timeout(500)

        # 点击免费围观按钮
        btn = page.locator('a:has-text("免费围观"), button:has-text("免费围观"), span:has-text("免费围观")').first
        if btn.count() > 0:
            btn.click()
            print("  [OK] 已点击'免费围观'")
            page.wait_for_timeout(3500)
        else:
            print("  [ERR] 找不到免费围观按钮")

    # --- 提取内容 ---
    data = extract_qa_content(page, url)
    if not data:
        print("  [ERR] 内容提取失败")
        return {}

    # --- 保存 ---
    q_text = sanitize_filename(data.get("question", "untitled"), 40)
    md_path = out_dir / f"{idx:03d}_{q_text}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {data.get('question', '未知问题')}\n\n")
        f.write(data.get("answer", "无回答内容"))
        f.write("\n")

    print(f"  [OK] 已保存: {md_path.name}")
    return data


# ==================== 内容提取（干净版） ====================
def extract_qa_content(page: Page, url: str) -> dict:
    result = {
        "url": url,
        "scraped_at": datetime.now().isoformat(),
        "question": "",
        "answer": "",
    }

    # 通过 JS 提取，优先使用微博问答的精确 class
    raw = page.evaluate(r"""() => {
        const r = {};
        // 1. 问题：从 .WB_answer_wrap 提取（找带问号或最长的有意义的文本块）
        const wrap = document.querySelector('.WB_answer_wrap');
        if (wrap) {
            const lines = wrap.innerText.trim().split('\n').map(x => x.trim()).filter(Boolean);
            // 策略：优先找包含"？"的行，且排除元数据
            const metaKeywords = ['问题价值', '人已围观', '￥'];
            let bestLine = '';
            for (const line of lines) {
                if (metaKeywords.some(k => line.includes(k))) continue;
                if (line.includes('？') && line.length > bestLine.length) {
                    bestLine = line;
                }
            }
            // 如果没找到带问号的，找最长的非元数据行
            if (!bestLine) {
                for (const line of lines) {
                    if (metaKeywords.some(k => line.includes(k))) continue;
                    if (line.length > bestLine.length) bestLine = line;
                }
            }
            r.question = bestLine;
        }
        // 2. 答案：从 .main_answer 提取
        const ans = document.querySelector('.main_answer');
        if (ans) {
            let lines = ans.innerText.trim().split('\n').map(x => x.trim()).filter(Boolean);
            // 去掉前缀 "你好"
            if (lines.length > 0 && lines[0] === '你好') {
                lines.shift();
            }
            // 去掉前缀 "真爱粉专属提问，以下为回答内容"
            const prefixIdx = lines.findIndex(l => l.includes('真爱粉专属提问'));
            if (prefixIdx !== -1) {
                lines = lines.slice(prefixIdx + 1);
            }
            // 去掉后缀：从 "@xxx 已围观" 或 "二总" 签名开始截断
            let endIdx = lines.length;
            for (let i = 0; i < lines.length; i++) {
                if (lines[i].includes('已围观') || lines[i] === '二总' || lines[i].includes('啥都不擅长') || lines[i] === '向Ta提问') {
                    endIdx = i;
                    break;
                }
            }
            lines = lines.slice(0, endIdx);
            r.answer = lines.join('\n');
        }
        return r;
    }""")

    if raw:
        result.update(raw)

    # 简单校验
    if not result["question"] or len(result["answer"]) < 10:
        return {}
    return result


# ==================== 主流程 ====================
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--login", action="store_true", help="先运行登录流程")
    parser.add_argument("--auto-collect", action="store_true", help="自动尝试收集文章链接")
    args = parser.parse_args()

    if args.login:
        do_login()
        return

    # 检查登录态
    if not STORAGE_STATE.exists():
        print("[ERR] 未找到登录态文件，请先运行: python erzong_vplus_scraper_v5.py --login")
        sys.exit(1)

    # 获取链接列表
    links = []
    if args.auto_collect:
        p, browser, context, page = launch_browser(headless=False)
        links = auto_collect_links(page)
        browser.close()
        p.stop()
        if not links:
            sys.exit(1)
    elif LINKS_FILE.exists():
        with open(LINKS_FILE, "r", encoding="utf-8") as f:
            links = [line.strip() for line in f if line.strip()]
        print(f"[MODE] 从 {LINKS_FILE} 读取了 {len(links)} 个链接")
    else:
        print(f"[ERR] 未找到链接文件: {LINKS_FILE}")
        print("请用以下方式之一提供链接：")
        print(f"  1. 手动写入文件: {LINKS_FILE}")
        print("  2. 运行自动收集: python erzong_vplus_scraper_v5.py --auto-collect")
        sys.exit(1)

    # 开始批量提取
    visited = load_visited()
    out_dir = ensure_output_dir()
    jsonl_path = out_dir / "qa.jsonl"

    p, browser, context, page = launch_browser(headless=False)
    total = len(links)
    processed = 0

    try:
        for idx, url in enumerate(links, 1):
            if url in visited:
                print(f"[{idx}/{total}] 已跳过（断点续传）: {url}")
                continue
            data = process_single_qa(page, url, idx, total, out_dir)
            if data:
                with open(jsonl_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(data, ensure_ascii=False) + "\n")
                visited.add(url)
                save_visited(visited)
                processed += 1
            # 随机间隔，模拟人类
            time.sleep(1.5 + (idx % 2) * 0.8)
    except KeyboardInterrupt:
        print("\n[INFO] 用户中断，已保存断点")
    finally:
        browser.close()
        p.stop()

    print(f"\n[OK] 完成！本次处理 {processed} 个，总计已处理 {len(visited)} 个")
    print(f"[OK] 输出目录: {out_dir}")


if __name__ == "__main__":
    main()
