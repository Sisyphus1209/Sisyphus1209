# 📰 AI 新闻秘书

你的个人智能新闻助理，每天定时推送精选全球新闻，附带专业注解。

## ✨ 功能特性

- **📂 四大领域覆盖**
  - 科技/AI
  - 财经/金融
  - 国际时政
  - 机器人/减速器行业

- **🚀 马斯克X监控**
  - 实时监控马斯克动态
  - 重要推文第一时间推送

- **🌐 全球英文媒体**
  - TechCrunch, The Verge, Wired
  - BBC, Reuters, NPR
  - IEEE Robotics, The Robot Report

- **📖 智能注解系统**
  - 专业术语解释
  - 人物背景介绍
  - 历史事件背景
  - 行业概念科普

- **⏰ 定时推送**
  - 每天早上 8:00
  - 每天晚上 8:00
  - Markdown 格式报告

## 🚀 快速开始

### 1. 安装依赖

```bash
cd news_assistant
pip install -r requirements.txt
```

### 2. 启动方式

**方式A：双击启动（推荐）**
双击 `start.bat`，选择操作：
- 立即获取早间/晚间新闻
- 启动定时服务
- 设置每天自动推送

**方式B：命令行**
```bash
# 立即获取早间新闻
python main.py --once

# 立即获取晚间新闻
python main.py --once --evening

# 启动定时服务（保持运行）
python main.py
```

### 3. 设置自动推送

```bash
# 创建定时任务（需要管理员权限）
python setup_scheduler.py

# 或在 start.bat 中选择选项 4
```

设置完成后，每天 8:00 和 20:00 会自动推送新闻。

## 📁 项目结构

```
news_assistant/
├── config.py           # 配置文件（新闻源、关键词等）
├── news_fetcher.py     # 新闻抓取模块
├── translator.py       # 翻译和注解模块
├── main.py            # 主程序
├── setup_scheduler.py  # 定时任务设置
├── start.bat          # 一键启动脚本
├── requirements.txt   # 依赖列表
└── news_reports/      # 生成的报告目录
```

## ⚙️ 自定义配置

编辑 `config.py` 可以：

- 添加/删除新闻类别
- 修改关键词
- 添加 RSS 订阅源
- 调整推送时间
- 设置输出格式

### 添加新的新闻源

在 `NEWS_CATEGORIES` 中添加：

```python
"新类别": {
    "name": "类别名称",
    "keywords": ["关键词1", "关键词2"],
    "rss_feeds": [
        "https://example.com/feed.xml",
    ]
}
```

### 添加专业术语注解

在 `translator.py` 的 `_load_term_dict()` 中添加：

```python
"新术语": "术语解释",
```

## 📄 报告示例

生成的报告包含：

```markdown
# 📰 全球新闻简报 - 早间版 (2026年4月5日 08:00)

## 🚀 马斯克动态监控
**08:15**
> Tesla FSD v12 即将推送给更多用户...

---

## 📂 科技/AI

### 1. OpenAI 发布 GPT-5 预览
*TechCrunch* | 07:30

**摘要**: OpenAI 在开发者大会上展示了 GPT-5 的新功能...

**💡 知识点**:
- 📖 **GPT**: 生成式预训练转换器 (Generative Pre-trained Transformer)...
- 📚 背景知识：大语言模型是近年来 AI 领域最重要的突破...

[阅读原文](https://...)
```

## 🔮 未来扩展

- [ ] 接入 X API 实现真正的马斯克监控
- [ ] 接入 AI 翻译 API 实现自动翻译
- [ ] 微信推送集成
- [ ] 邮件推送集成
- [ ] 语音播报功能
- [ ] 个性化推荐算法

## 📝 注意事项

1. **网络要求**: 需要能访问国际网站
2. **RSS 源**: 部分 RSS 源可能需要翻墙
3. **X 监控**: 当前为模拟实现，需要 X API Key 才能获取真实数据
4. **翻译**: 当前显示原文，可接入百度/谷歌翻译 API

## 📞 问题反馈

如有问题，请检查：
1. 依赖是否安装完整
2. 网络连接是否正常
3. RSS 源是否可访问
