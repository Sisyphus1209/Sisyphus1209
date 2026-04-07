#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 图纸工程批注工具
根据 AI 审图分析结果，在客户图纸上精准标注差异点。

用法:
  模式1（结构化JSON）:
    python pdf_annotate_from_analysis.py "客户图.pdf" "analysis.json"

  模式2（纯文本，复制Kimi回答）:
    python pdf_annotate_from_analysis.py "客户图.pdf" "analysis.txt" --text-mode

JSON输入格式示例:
  [
    {
      "target_keyword": "14-φ11通",
      "location_hint": "左上角法兰视图",
      "difference": "安装孔形式不同：客户图为通孔，公司标准图为盲孔（4-M6×10）",
      "severity": "重大差异"
    },
    {
      "target_keyword": "187.25",
      "location_hint": "中上剖视图输入端",
      "difference": "输入端轴向尺寸长出约 5mm，需确认电机/联轴器安装空间",
      "severity": "关键差异"
    }
  ]

纯文本输入格式示例（Kimi回答直接复制）:
  一、安装法兰接口（重大差异）
  结论：虽然分度圆均为φ233±0.1，但因安装孔形式完全不同（盲孔vs通孔）...

  二、输入端轴向尺寸（关键差异）
  风险点：改制版输入端长出5mm，可能导致与联轴器/电机的轴向干涉...

输出:
  - output/pdf_annotated/annotated_drawing.jpg
  - output/pdf_annotated/annotation_summary.md
"""

import argparse
import json
import re
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path("output/pdf_annotated")
DPI = 200


def pdf_page_to_image(pdf_path: str, page_idx: int = 0):
    doc = fitz.open(pdf_path)
    page = doc[page_idx]
    mat = fitz.Matrix(DPI / 72, DPI / 72)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img, doc


def find_keyword_positions(pdf_path: str, keywords: list, page_idx: int = 0):
    """在 PDF 中搜索一组关键词，返回最先匹配到的位置列表"""
    doc = fitz.open(pdf_path)
    page = doc[page_idx]
    scale = DPI / 72

    for keyword in keywords:
        results = []
        # 精确搜索
        text_instances = page.search_for(keyword)
        for inst in text_instances:
            x0, y0, x1, y1 = inst
            results.append((int(x0 * scale), int(y0 * scale), int(x1 * scale), int(y1 * scale)))
        if results:
            return results

        # 模糊搜索（去掉特殊字符）
        clean_kw = re.sub(r'[φΦ±°′"\s]', '', keyword)
        if clean_kw:
            blocks = page.get_text("blocks")
            for x0, y0, x1, y1, text, *_ in blocks:
                clean_text = re.sub(r'[φΦ±°′"\s]', '', text)
                if clean_kw in clean_text:
                    results.append((int(x0 * scale), int(y0 * scale), int(x1 * scale), int(y1 * scale)))
        if results:
            return results

    return []


def load_font(size: int = 22):
    for font_name in ["msyh.ttc", "simhei.ttf", "simsun.ttc", "arial.ttf"]:
        try:
            return ImageFont.truetype(font_name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def wrap_text(text: str, font, max_width: int) -> list:
    """将长文本按 max_width 像素宽度换行"""
    lines = []
    current = ""
    for char in text:
        test = current + char
        bbox = font.getbbox(test)
        w = bbox[2] - bbox[0]
        if w > max_width and current:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines if lines else [text]


def cluster_positions(positions, max_dist=280):
    """对匹配位置聚类，保留最大的邻近簇，过滤远离的误匹配"""
    if len(positions) <= 1:
        return positions
    centers = [((p[0] + p[2]) / 2, (p[1] + p[3]) / 2) for p in positions]
    best = []
    for i, c1 in enumerate(centers):
        cluster = []
        for j, c2 in enumerate(centers):
            dist = ((c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2) ** 0.5
            if dist <= max_dist:
                cluster.append(positions[j])
        if len(cluster) > len(best):
            best = cluster
    return best


def draw_annotation(img: Image.Image, positions, note_text: str, severity: str, note_idx: int):
    draw = ImageDraw.Draw(img)
    font = load_font(18)
    font_small = load_font(14)

    colors = {
        "重大差异": "#FF0000",
        "关键差异": "#FF6600",
        "重要差异": "#FFAA00",
        "一般差异": "#0066FF",
    }
    color = colors.get(severity, "#FF0000")

    prefix = f"【{note_idx}】"
    sev_text = f"({severity})"

    if not positions:
        return img

    # 聚类过滤
    positions = cluster_positions(positions)

    # 合并为一个包围框
    min_x = min(p[0] for p in positions)
    min_y = min(p[1] for p in positions)
    max_x = max(p[2] for p in positions)
    max_y = max(p[3] for p in positions)

    # 画合并红框
    padding = 6
    draw.rectangle(
        [min_x - padding, min_y - padding, max_x + padding, max_y + padding],
        outline=color, width=3
    )

    # 文字换行（限制最大宽度 450px）
    max_text_w = 450
    wrapped = wrap_text(prefix + note_text, font, max_text_w)
    full_text = "\n".join(wrapped)

    # 计算文字块尺寸
    line_heights = []
    max_line_w = 0
    for line in wrapped:
        bbox = draw.textbbox((0, 0), line, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        max_line_w = max(max_line_w, w)
        line_heights.append(h)
    tw = max_line_w
    th = sum(line_heights) + 4 * (len(wrapped) - 1)

    # 选择批注位置：优先放在包围框的右上方或左上方
    candidates = [
        (max_x + 20, min_y - th - 15),           # 右上方
        (min_x - tw - 25, min_y - th - 15),      # 左上方
        (max_x + 20, max_y + 15),                 # 右下方
        (min_x - tw - 25, max_y + 15),            # 左下方
        (50, 50 + note_idx * 80),                  # 兜底：左上角
    ]

    ax, ay = None, None
    for cx, cy in candidates:
        if 10 <= cx <= img.width - tw - 10 and 10 <= cy <= img.height - th - 10:
            ax, ay = cx, cy
            break
    if ax is None:
        ax, ay = 50, 50 + note_idx * 80

    # 箭头从批注框指向合并框的最近点
    target_cx = (min_x + max_x) // 2
    target_cy = (min_y + max_y) // 2
    # 找批注框边界上离目标最近的点
    note_cx = ax + tw // 2
    note_cy = ay + th // 2
    draw.line([(note_cx, note_cy), (target_cx, target_cy)], fill=color, width=2)

    # 画文字背景
    padding_bg = 8
    draw.rectangle(
        [ax - padding_bg, ay - padding_bg, ax + tw + padding_bg, ay + th + padding_bg],
        fill="white", outline=color
    )

    # 写文字
    y_offset = ay
    for line in wrapped:
        draw.text((ax, y_offset), line, fill=color, font=font)
        bbox = draw.textbbox((0, 0), line, font=font)
        y_offset += (bbox[3] - bbox[1]) + 4

    # 严重度小标签（放在批注框下方或右侧）
    if sev_text:
        sx, sy = ax, y_offset + 4
        bbox_s = draw.textbbox((0, 0), sev_text, font=font_small)
        sw, sh = bbox_s[2] - bbox_s[0], bbox_s[3] - bbox_s[1]
        draw.rectangle([sx, sy, sx + sw + 6, sy + sh + 4], fill=color)
        draw.text((sx + 3, sy + 1), sev_text, fill="white", font=font_small)

    return img


def parse_text_analysis(text_path: str):
    """从纯文本（Kimi回答）解析出差异点列表"""
    content = Path(text_path).read_text(encoding="utf-8")
    items = []

    # 新策略：先找到所有 "数字. 标题（严重度）" 的标题行，然后切分内容块
    header_pattern = re.compile(
        r'^(\d+\.\s*)(.*?)(?:[（(](.*?)[)）])?\s*$',
        re.MULTILINE
    )

    matches = list(header_pattern.finditer(content))
    for i, m in enumerate(matches):
        title = m.group(2).strip()
        severity = m.group(3).strip() if m.group(3) else "差异"
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        block = content[start:end].strip()

        # 截断：如果 block 里出现中文章节标题（如"三、互换性建议"），在那里截断
        section_cut = re.search(r'\n[一二三四五六七八九十]+[、.\s]+.*?\n', '\n' + block + '\n')
        if section_cut:
            block = block[:section_cut.start()].strip()

        lines = [ln.strip() for ln in block.split('\n') if ln.strip()]
        diff_clean = ' '.join(lines)

        # 如果 block 为空或很短，用标题补充
        if len(diff_clean) < 5:
            diff_clean = title

        # 限制单条差异长度（避免把整篇文章吞进去）
        if len(diff_clean) > 300:
            diff_clean = diff_clean[:297] + "..."

        items.append({
            "target_keywords": guess_keywords(title, diff_clean),
            "location_hint": title,
            "difference": diff_clean,
            "severity": severity
        })

    # 兜底：如果没匹配到任何结构化标题，退化为按行提取
    if not items:
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if '：' in line and len(line) > 15:
                parts = line.split('：', 1)
                title_part = parts[0]
                diff_part = parts[1]
                severity = "差异"
                for k in ["重大", "关键", "重要", "一般"]:
                    if k in title_part:
                        severity = k + "差异"
                        break
                items.append({
                    "target_keywords": guess_keywords(title_part, diff_part),
                    "location_hint": title_part,
                    "difference": diff_part,
                    "severity": severity
                })

    return items


def guess_keywords(title: str, diff: str) -> list:
    """根据标题和差异描述，猜测一组候选关键词用于图纸上定位"""
    candidates = []

    # 特殊关键词映射（按优先级）
    if "法兰" in title or "安装孔" in title:
        candidates = ["14-φ11", "φ11", "9-M12", "M12×20", "6-M6", "2-M6"]
    elif "轴向" in title or "输入端" in title:
        candidates = ["187.25", "190.75", "21.15MAX", "21.15"]
    elif "速比" in title or "齿轮" in title:
        candidates = ["36.75", "m=1.75", "z=33", "107/33", "107"]
    elif "标记" in title or "螺纹孔" in title:
        candidates = ["标记", "4-M6", "2-M6", "M6深10"]
    elif "输出端" in title:
        candidates = ["壳输出", "轴输出", "39.35", "φ195.7", "Rc1/8"]

    # 通用提取：φ 尺寸
    phi = re.findall(r'φ\d+[\d.±]*', diff)
    for p in phi:
        if p not in candidates:
            candidates.append(p)

    # M 螺纹
    m_thread = re.findall(r'M\d+[×x]\d+', diff)
    for m in m_thread:
        if m not in candidates:
            candidates.append(m)

    # 特殊数字（长度/直径类优先）
    nums = re.findall(r'\b\d{2,3}(?:\.\d{1,2})?\b', diff)
    for n in nums:
        if n not in candidates and n not in ["107", "33", "6000", "980", "2450", "4900"]:
            candidates.append(n)

    return candidates


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf_path", help="客户图纸 PDF 路径")
    parser.add_argument("analysis_path", help="分析结果文件 (.json 或 .txt)")
    parser.add_argument("--text-mode", action="store_true", help="分析文件是纯文本模式")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 加载分析结果
    analysis_ext = Path(args.analysis_path).suffix.lower()
    if analysis_ext == ".json" or not args.text_mode:
        try:
            items = json.loads(Path(args.analysis_path).read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            items = parse_text_analysis(args.analysis_path)
    else:
        items = parse_text_analysis(args.analysis_path)

    if not items:
        print("[ERR] 未能从分析文件中解析出任何差异点。")
        sys.exit(1)

    print(f"[INFO] 解析到 {len(items)} 个差异点")

    # 2. 加载客户图纸
    img, _ = pdf_page_to_image(args.pdf_path)

    # 3. 逐条标注
    summary_lines = ["# 图纸差异标注汇总\n", f"**图纸**: {Path(args.pdf_path).name}\n\n"]
    placed_notes = []

    for idx, item in enumerate(items, 1):
        keywords = item.get("target_keywords", [])
        diff = item.get("difference", "")
        severity = item.get("severity", "差异")
        hint = item.get("location_hint", "")

        print(f"[{idx}] 正在标注: {hint or diff[:30]}...")
        positions = find_keyword_positions(args.pdf_path, keywords) if keywords else []

        if positions:
            print(f"      找到关键词 '{keywords[0]}'，位置: {len(positions)} 处")
            img = draw_annotation(img, positions, diff, severity, idx)
            summary_lines.append(f"**【{idx}】{severity}** — {diff}\n- 定位关键词: `{keywords[0] if keywords else '无'}`\n\n")
        else:
            # 找不到具体位置，汇总到左上角列表
            placed_notes.append((idx, severity, diff))
            print(f"      未找到关键词 {keywords[:3]}，将加入左上角汇总")
            summary_lines.append(f"**【{idx}】{severity}** — {diff}\n- 未能在图上自动定位，请手动核对\n\n")

    # 4. 在左上角画汇总列表（针对找不到位置的项目）
    if placed_notes:
        draw = ImageDraw.Draw(img)
        font = load_font(18)
        y_start = 30
        for idx, severity, diff in placed_notes:
            text = f"【{idx}】{severity}: {diff[:40]}..."
            bbox = draw.textbbox((0, 0), text, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.rectangle([20, y_start, 30 + tw, y_start + th + 8], fill="white", outline="#FF0000")
            draw.text((25, y_start + 3), text, fill="#FF0000", font=font)
            y_start += th + 15

    # 5. 保存
    out_img = OUTPUT_DIR / "annotated_drawing.jpg"
    img.save(out_img, quality=95)

    out_md = OUTPUT_DIR / "annotation_summary.md"
    out_md.write_text("".join(summary_lines), encoding="utf-8")

    print(f"\n[OK] 标注完成！")
    print(f"     批注图: {out_img}")
    print(f"     汇总报告: {out_md}")


if __name__ == "__main__":
    import sys
    main()
