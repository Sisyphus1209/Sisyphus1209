---
name: watermark-killer
description: |
  当用户需要批量去除 PDF 或图片中的水印时，使用此 skill。
  触发词：「去水印」「PDF 去水印」「批量去水印」「watermark remove」「
  清除水印」「kill watermark」「文档水印」
---

# Watermark Killer

## 使用说明

提供两套 PowerShell 脚本，分别处理不同场景的水印去除。

## 脚本说明

### 1. remove_watermark.ps1

基础版水印去除。用法：

```powershell
.\scripts\remove_watermark.ps1 -InputFile "document.pdf"
```

### 2. watermark_killer.ps1

高级版，支持批量处理、更多水印类型识别与清除。

```powershell
.\scripts\watermark_killer.ps1 -InputPath "C:\Documents" -OutputPath "C:\Cleaned"
```

## 支持格式

- PDF 文档（扫描件和原生 PDF 的处理策略不同）
- 图片文件（PNG / JPG / BMP）

## 诚实边界

- 水印去除效果取决于水印与正文的对比度和叠加方式
- 复杂水印（如全屏半透明底纹、与正文颜色接近的文字）可能无法完全清除
- 仅用于个人合法拥有的文档处理，请勿用于侵犯版权的非法用途
