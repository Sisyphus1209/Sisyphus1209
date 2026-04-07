#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 图纸智能对比工具 (Smart Mode)
用法: python pdf_compare_smart.py "公司图.pdf" "客户图.pdf"
输出:
  - output/pdf_compare_smart/annotated_customer_drawing.jpg  (在客户图上批注差异)
  - output/pdf_compare_smart/smart_report.md                  (结构化差异报告)
"""

import sys
import difflib
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = Path("output/pdf_compare_smart")
DPI = 200


def pdf_page_to_image(pdf_path: str, page_idx: int = 0):
    """将指定页转为 PIL Image (RGB)"""
    doc = fitz.open(pdf_path)
    page = doc[page_idx]
    mat = fitz.Matrix(DPI / 72, DPI / 72)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img, doc


def extract_text_blocks(pdf_path: str, page_idx: int = 0):
    """提取文字块，返回 (x0, y0, x1, y1, text) 列表"""
    doc = fitz.open(pdf_path)
    page = doc[page_idx]
    blocks = page.get_text("dict")["blocks"]
    result = []
    for b in blocks:
        if "lines" not in b:
            continue
        for line in b["lines"]:
            for span in line["spans"]:
                x0, y0, x1, y1 = span["bbox"]
                text = span["text"].strip()
                if text:
                    result.append((x0, y0, x1, y1, text))
    # 按 y 再按 x 排序
    result.sort(key=lambda t: (t[1], t[0]))
    return result


def identify_zones(blocks, page_width: float, page_height: float):
    """根据位置和内容识别关键区域"""
    zones = {
        "title_block": {"texts": [], "bboxes": []},   # 标题栏：右下角
        "param_table": {"texts": [], "bboxes": []},   # 参数表：表格密集区
        "tech_notes":  {"texts": [], "bboxes": []},   # 技术要求：含"注"字
        "dimensions":  {"texts": [], "bboxes": []},   # 尺寸标注：含φ M ±
        "other":       {"texts": [], "bboxes": []},   # 其他
    }

    # 区域边界判断
    right_x = page_width * 0.65
    bottom_y = page_height * 0.80

    for x0, y0, x1, y1, text in blocks:
        # 标题栏：右下角区域 + 常见关键词
        if x0 > right_x and y0 > bottom_y:
            keywords = ["设计", "校对", "审核", "批准", "比例", "数量", "版本", "标记", "处数", "签名"]
            if any(k in text for k in keywords) or (x0 > page_width * 0.8 and y0 > page_height * 0.85):
                zones["title_block"]["texts"].append(text)
                zones["title_block"]["bboxes"].append((x0, y0, x1, y1))
                continue

        # 技术要求
        if text.startswith("注：") or text.startswith("注:") or "技术要求" in text:
            zones["tech_notes"]["texts"].append(text)
            zones["tech_notes"]["bboxes"].append((x0, y0, x1, y1))
            continue

        # 参数表：纯数字、单位、或常见参数关键词，且通常集中在中上部或右侧中部
        param_keywords = ["减速比", "转矩", "转速", "齿隙", "精度", "寿命", "容许", "额定", "输入", "输出", "arcmin", "r/min", "Nm", "h"]
        is_numeric = text.replace(".", "").replace("-", "").replace("+", "").replace("<", "").isdigit()
        if (is_numeric or any(k in text for k in param_keywords)) and (y0 < page_height * 0.6 or x0 > page_width * 0.5):
            zones["param_table"]["texts"].append(text)
            zones["param_table"]["bboxes"].append((x0, y0, x1, y1))
            continue

        # 尺寸标注：含机械符号
        dim_symbols = ["φ", "Φ", "M", "±", "°", "′", '"', "MAX", "MIN"]
        if any(s in text for s in dim_symbols):
            zones["dimensions"]["texts"].append(text)
            zones["dimensions"]["bboxes"].append((x0, y0, x1, y1))
            continue

        zones["other"]["texts"].append(text)
        zones["other"]["bboxes"].append((x0, y0, x1, y1))

    return zones


def zone_diff(zone_name, texts_a, texts_b):
    """对两个区域做文字diff，返回 (has_diff, summary_lines, added_lines, removed_lines)"""
    a_str = "\n".join(texts_a)
    b_str = "\n".join(texts_b)
    if a_str == b_str:
        return False, [], [], []

    diff = list(difflib.unified_diff(texts_a, texts_b, lineterm="", fromfile="公司图", tofile="客户图"))
    added = [line[1:] for line in diff if line.startswith("+") and not line.startswith("+++")]
    removed = [line[1:] for line in diff if line.startswith("-") and not line.startswith("---")]

    summary = [f"**{zone_name}** 存在差异："]
    if added:
        summary.append(f"- 客户图新增 {len(added)} 项内容")
    if removed:
        summary.append(f"- 客户图缺失 {len(removed)} 项内容（公司图有）")
    return True, summary, added, removed


def draw_annotation(img: Image.Image, bboxes, note_text: str, color="red", offset=(20, -40)):
    """在客户图上画红框和批注"""
    draw = ImageDraw.Draw(img)
    # 尝试加载中文字体
    font = None
    for font_name in ["msyh.ttc", "simhei.ttf", "simsun.ttc", "arial.ttf"]:
        try:
            font = ImageFont.truetype(font_name, 24)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()

    for x0, y0, x1, y1 in bboxes:
        # 坐标从 PDF 点转换到像素（假设 72 DPI -> 200 DPI）
        scale = DPI / 72
        px0, py0, px1, py1 = int(x0 * scale), int(y0 * scale), int(x1 * scale), int(y1 * scale)
        draw.rectangle([px0, py0, px1, py1], outline=color, width=3)

        # 批注位置：框的右上方
        ax, ay = px1 + offset[0], py0 + offset[1]
        # 如果超出边界，放到左上方
        if ax + 200 > img.width:
            ax = px0 - 220
        if ay < 0:
            ay = py1 + 10

        # 画箭头线
        draw.line([(px1, py0), (ax + 10, ay + 10)], fill=color, width=2)
        # 写文字（带小背景框）
        bbox_text = draw.textbbox((0, 0), note_text, font=font)
        tw, th = bbox_text[2] - bbox_text[0], bbox_text[3] - bbox_text[1]
        draw.rectangle([ax - 4, ay - 4, ax + tw + 8, ay + th + 8], fill="white", outline=color)
        draw.text((ax, ay), note_text, fill=color, font=font)

    return img


def main():
    if len(sys.argv) != 3:
        print("用法: python pdf_compare_smart.py \"公司图.pdf\" \"客户图.pdf\"")
        sys.exit(1)

    pdf_a = sys.argv[1]  # 公司图
    pdf_b = sys.argv[2]  # 客户图
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("[1/4] 正在提取两本图纸的文字块...")
    blocks_a = extract_text_blocks(pdf_a)
    blocks_b = extract_text_blocks(pdf_b)

    # 获取页面尺寸（用于区域划分）
    doc_a = fitz.open(pdf_a)
    page_a = doc_a[0]
    pw, ph = page_a.rect.width, page_a.rect.height

    print("[2/4] 正在识别关键区域...")
    zones_a = identify_zones(blocks_a, pw, ph)
    zones_b = identify_zones(blocks_b, pw, ph)

    print("[3/4] 正在对比各区域差异并生成批注图...")
    img_b, _ = pdf_page_to_image(pdf_b)  # 客户图作为底图

    report_lines = ["# 图纸智能对比报告（Smart Mode）\n"]
    report_lines.append("- **左侧（公司标准图）**: {}\n".format(Path(pdf_a).name))
    report_lines.append("- **右侧（客户提供图）**: {}\n".format(Path(pdf_b).name))
    report_lines.append(f"- **图纸尺寸**: {pw:.0f} x {ph:.0f} pt\n\n")

    zone_names = {
        "title_block": "标题栏",
        "param_table": "参数表/性能表",
        "tech_notes":  "技术要求/注释",
        "dimensions":  "尺寸标注",
        "other":       "其他文字",
    }

    has_any_diff = False
    for key, cn_name in zone_names.items():
        texts_a = zones_a[key]["texts"]
        texts_b = zones_b[key]["texts"]
        diff_flag, summary, added, removed = zone_diff(cn_name, texts_a, texts_b)
        if diff_flag:
            has_any_diff = True
            print(f"      [{cn_name}] 发现差异")
            report_lines.append("## {}\n".format(cn_name))
            report_lines.extend([s + "\n" for s in summary])
            if added:
                report_lines.append("\n**客户图新增内容：**\n")
                report_lines.append("```\n" + "\n".join(added) + "\n```\n")
            if removed:
                report_lines.append("\n**公司图有但客户图缺失：**\n")
                report_lines.append("```\n" + "\n".join(removed) + "\n```\n")
            report_lines.append("\n")

            # 在客户图上标注新增内容的 bbox
            if added and zones_b[key]["bboxes"]:
                note = f"与公司图不同: {added[0][:20]}..." if len(added[0]) > 20 else f"与公司图不同: {added[0]}"
                img_b = draw_annotation(img_b, zones_b[key]["bboxes"], note)

    if not has_any_diff:
        report_lines.append("> 未检测到关键区域差异。\n")

    # 保存批注图
    annotated_path = OUTPUT_DIR / "annotated_customer_drawing.jpg"
    img_b.save(annotated_path, quality=95)

    # 保存报告
    report_path = OUTPUT_DIR / "smart_report.md"
    report_path.write_text("".join(report_lines), encoding="utf-8")

    print(f"\n[OK] 全部完成！输出目录: {OUTPUT_DIR.resolve()}")
    print(f"     批注图: {annotated_path}")
    print(f"     报告:   {report_path}")


if __name__ == "__main__":
    main()
