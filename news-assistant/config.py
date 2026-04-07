#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻秘书配置文件
"""

# 新闻题材领域配置
NEWS_CATEGORIES = {
    "tech_ai": {
        "name": "科技/AI",
        "keywords": ["AI", "artificial intelligence", "machine learning", "ChatGPT", "LLM", 
                     "robotics", "automation", "semiconductor", "chip", "NVIDIA"],
        "rss_feeds": [
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml",
            "https://www.wired.com/feed/rss",
            "https://arstechnica.com/feed/",
        ]
    },
    "finance": {
        "name": "财经/金融",
        "keywords": ["stock market", "Federal Reserve", "inflation", "economy", 
                     "investment", "trading", "cryptocurrency", "bitcoin", "ETF"],
        "rss_feeds": [
            "https://feeds.bbci.co.uk/news/business/rss.xml",
            "https://feeds.marketwatch.com/marketwatch/topstories/",
        ]
    },
    "politics": {
        "name": "国际时政",
        "keywords": ["US China", "trade war", "sanctions", "diplomacy", "Biden", 
                     "Trump", "UN", "NATO", "Middle East", "Taiwan"],
        "rss_feeds": [
            "https://feeds.bbci.co.uk/news/world/rss.xml",
            "https://feeds.npr.org/1001/rss.xml",
        ]
    },
    "robotics": {
        "name": "机器人/减速器",
        "keywords": ["robot", "industrial robot", "RV reducer", "harmonic drive", 
                     "Tesla Bot", "Optimus", "humanoid robot", "automation", "manufacturing"],
        "rss_feeds": [
            "https://www.therobotreport.com/feed/",
            "https://robotics.ieee.org/news/feed/",
        ]
    },
    "devtools": {
        "name": "Skills / MCP / CLI 生态",
        "keywords": ["MCP", "Model Context Protocol", "skill", "CLI", "plugin", 
                     "extension", "developer tool", "agent", "AI coding", "workflow"],
        "rss_feeds": [
            # 使用 GitHub / Reddit / HN Algolia 免费 API，无需 token
        ],
        "free_apis": [
            "github_trending_mcp",
            "reddit_mcp",
            "hackernews_mcp",
        ]
    }
}

# 马斯克X监控配置
ELON_CONFIG = {
    "username": "elonmusk",
    "name": "马斯克",
    "keywords": ["Tesla", "SpaceX", "X", "Twitter", "DOGE", "crypto", "AI", 
                 "Grok", "Neuralink", "Boring Company", "Mars", "Optimus"],
    "check_interval_minutes": 30,  # 每30分钟检查一次
}

# 推送配置
PUSH_CONFIG = {
    "morning_time": "08:00",  # 早上推送时间
    "evening_time": "20:00",  # 晚上推送时间
    "max_news_per_category": 5,  # 每个类别最多几条新闻
    "max_elon_tweets": 10,  # 马斯克最多几条推文
}

# 报告输出配置
OUTPUT_CONFIG = {
    "output_dir": "news_reports",  # 报告保存目录
    "format": "markdown",  # 输出格式: markdown, html
    "keep_history_days": 30,  # 保留历史天数
}

# 翻译配置
TRANSLATION_CONFIG = {
    "target_language": "zh-CN",
    "translate_title": True,
    "translate_summary": True,
}

# 翻译 API 配置
TRANSLATION_API_CONFIG = {
    "provider": "deepseek",  # 可选: deepseek, mymemory, none
    "api_key": "sk-e397d5826047438e87705e0b3e5e5341",  # DeepSeek API Key
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "max_tokens": 8192,
}

# 微博搜索配置
WEIBO_CONFIG = {
    "enabled": True,
    "keywords": ["MCP", "AI工具", "开源技能", "CLI神器", "编程技巧", "大模型"],
    "storage_state": r"C:\Users\Administrator\weibo_crawler\output\weibo_storage_state.json",
    "max_results_per_keyword": 5,
}

# 注解配置
ANNOTATION_CONFIG = {
    "enabled": True,
    "explain_terms": True,  # 解释专业术语
    "explain_history": True,  # 解释历史背景
    "explain_people": True,  # 解释人物背景
}
