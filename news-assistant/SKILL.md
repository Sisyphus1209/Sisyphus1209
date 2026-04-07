---
name: news-assistant
description: |
  当用户需要获取全球新闻简报、启动 AI 新闻秘书服务、配置定时推送、
  或查看马斯克 X 动态监控时，使用此 skill。
  触发词：「早间新闻」「晚间新闻」「新闻秘书」「马斯克动态」「
  启动新闻服务」「今天有什么新闻」「机器人行业新闻」「AI新闻」
---

# AI 新闻秘书

> 个人智能新闻助理。每天 8:00 / 20:00 定时推送精选全球新闻，附带专业术语注解。

## 快速使用

### 立即获取新闻

```bash
cd news-assistant
python main.py --once          # 早间新闻
python main.py --once --evening # 晚间新闻
```

### 启动定时服务（常驻）

```bash
python main.py
```

或双击 `start.bat` 选择启动定时服务。

### 设置 Windows 自动任务

```bash
python setup_scheduler.py
```

## 覆盖领域

| 领域 | 代表源 |
|------|--------|
| 科技/AI | TechCrunch, The Verge, Wired |
| 财经/金融 | Reuters, BBC Business |
| 国际时政 | BBC, NPR, Reuters |
| 机器人/减速器 | IEEE Robotics, The Robot Report |

## 马斯克 X 监控

- `elon_fetcher.py` / `elon_scraper.py` 负责拉取马斯克动态
- 重要推文会单独列在报告首位

## 输出格式

所有报告生成在 `news_reports/` 目录下，Markdown 格式，包含：
- 新闻摘要（原文 + 标题 + 来源 + 时间）
- 专业术语注解（💡 知识点）
- 分类目录
- 马斯克动态专区

## 配置入口

编辑 `config.py` 可自定义：
- RSS 订阅源
- 关键词过滤
- 推送时间
- 输出格式

## 依赖

```bash
pip install -r requirements.txt
```

## 诚实边界

- 部分 RSS 源需要国际网络访问
- 马斯克 X 监控当前依赖公开抓取，非官方 X API
- 翻译/注解模块可接入 DeepSeek / 百度 / Google API 进一步提升质量
