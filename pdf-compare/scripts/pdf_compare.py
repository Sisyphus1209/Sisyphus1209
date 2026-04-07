#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF 图纸对比工具
用法: python pdf_compare.py "公司图.pdf" "客户图.pdf"
输出:
  - output/pdf_compare/page_XX_diff.jpg  (带红框标注的左右对比图)
  - output/pdf_compare/diff_report.md    (文字差异报告)
"""

import sys
import difflib
from pathlib import Path

import fitz  # PyMuPDF
import cv2
import numpy as np

OUTPUT_DIR = Path("output/pdf_compare")
DPI = 200  # 图纸建议 200 DPI，兼顾清晰度与速度


def pdf_to_images(pdf_path: str):
    """将 PDF 每一页转为 RGB numpy 数组"""
    doc = fitz.open(pdf_path)
    images = []
    for page in doc:
        mat = fitz.Matrix(DPI / 72, DPI / 72)
        pix = page.get_pixmap(matrix=mat)
        img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
        # PyMuPDF 可能是 RGBA，转成 RGB
        if img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
        images.append(img)
    return images, doc


def compare_pages(img_a, img_b):
    """对比两页图像，返回带红框的标注图和差异轮廓列表"""
    # 统一尺寸（取交集尺寸，避免微小差异导致错位）
    h = min(img_a.shape[0], img_b.shape[0])
    w = min(img_a.shape[1], img_b.shape[1])
    img_a = cv2.resize(img_a, (w, h))
    img_b = cv2.resize(img_b, (w, h))

    # 灰度化 → 差分
    gray_a = cv2.cvtColor(img_a, cv2.COLOR_RGB2GRAY)
    gray_b = cv2.cvtColor(img_b, cv2.COLOR_RGB2GRAY)
    diff = cv2.absdiff(gray_a, gray_b)

    # 二值化：差异大于 30 视为不同（图纸背景白，线条黑，30 足够敏感）
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)

    # 形态学闭运算：把破碎的差异块连起来；开运算：去掉微小噪点
    kernel = np.ones((5, 5), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)

    # 找差异区域轮廓
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 画红框（仅画面积足够大的）
    ann_a = img_a.copy()
    ann_b = img_b.copy()
    valid_contours = []
    for cnt in contours:
        x, y, bw, bh = cv2.boundingRect(cnt)
        if bw > 25 and bh > 25:
            cv2.rectangle(ann_a, (x, y), (x + bw, y + bh), (255, 0, 0), 3)
            cv2.rectangle(ann_b, (x, y), (x + bw, y + bh), (255, 0, 0), 3)
            valid_contours.append(cnt)

    return ann_a, ann_b, valid_contours, (h, w)


def extract_texts(pdf_path: str):
    """提取 PDF 每一页的全部文字"""
    doc = fitz.open(pdf_path)
    return [page.get_text() for page in doc]


def generate_report(texts_a, texts_b, diff_counts):
    """生成 Markdown 文字差异报告"""
    lines = []
    lines.append("# 图纸差异报告\n")
    lines.append("- **左侧（红框图左半）**: 公司标准图纸\n")
    lines.append("- **右侧（红框图右半）**: 客户提供图纸\n")
    lines.append(f"- **总页数对比**: 公司图 {len(texts_a)} 页 vs 客户图 {len(texts_b)} 页\n\n")

    pages = min(len(texts_a), len(texts_b))
    for i in range(pages):
        lines.append(f"## 第 {i + 1} 页\n")
        lines.append(f"**视觉差异区域数**: {diff_counts[i]}\n\n")

        diff = list(difflib.unified_diff(
            texts_a[i].splitlines(),
            texts_b[i].splitlines(),
            lineterm="",
            fromfile="公司图",
            tofile="客户图"
        ))
        if diff:
            lines.append("### 文字差异\n")
            lines.append("```diff\n")
            lines.append("\n".join(diff))
            lines.append("\n```\n\n")
        else:
            lines.append("文字内容完全一致。\n\n")

    if len(texts_a) != len(texts_b):
        lines.append("> **注意**: 两本图纸页数不一致，仅对比了前 {} 页。\n".format(pages))

    report_path = OUTPUT_DIR / "diff_report.md"
    report_path.write_text("".join(lines), encoding="utf-8")
    return report_path


def main():
    if len(sys.argv) != 3:
        print("用法: python pdf_compare.py \"公司图.pdf\" \"客户图.pdf\"")
        sys.exit(1)

    pdf_a = sys.argv[1]  # 公司图
    pdf_b = sys.argv[2]  # 客户图

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("[1/4] 正在将 PDF 转为高清图片...")
    imgs_a, doc_a = pdf_to_images(pdf_a)
    imgs_b, doc_b = pdf_to_images(pdf_b)
    print(f"      公司图: {len(imgs_a)} 页 | 客户图: {len(imgs_b)} 页")

    print("[2/4] 正在逐页图像对比并画红框...")
    diff_counts = []
    pages = min(len(imgs_a), len(imgs_b))
    for i in range(pages):
        ann_a, ann_b, contours, (h, w) = compare_pages(imgs_a[i], imgs_b[i])
        diff_counts.append(len(contours))
        print(f"      第 {i + 1:02d} 页: 发现 {len(contours)} 处差异")

        # 合成左右对比图（中间留 10px 白缝）
        canvas_w = w * 2 + 10
        canvas = np.full((h, canvas_w, 3), 255, dtype=np.uint8)
        canvas[:ann_a.shape[0], :ann_a.shape[1]] = ann_a
        canvas[:ann_b.shape[0], w + 10:w + 10 + ann_b.shape[1]] = ann_b

        out_img = OUTPUT_DIR / f"page_{i + 1:02d}_diff.jpg"
        cv2.imwrite(str(out_img), cv2.cvtColor(canvas, cv2.COLOR_RGB2BGR))

    print("[3/4] 正在提取图纸文字...")
    texts_a = extract_texts(pdf_a)
    texts_b = extract_texts(pdf_b)

    print("[4/4] 正在生成差异报告...")
    report_path = generate_report(texts_a, texts_b, diff_counts)

    print(f"\n[OK] 全部完成！输出目录: {OUTPUT_DIR.resolve()}")
    print(f"     标注对比图: {OUTPUT_DIR / 'page_01_diff.jpg'} 等")
    print(f"     文字报告: {report_path}")


if __name__ == "__main__":
    main()
