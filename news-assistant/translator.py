#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
翻译和注解模块
使用本地 LLM 或在线翻译服务
"""

import re
from typing import List, Dict
from dataclasses import dataclass
import json


@dataclass
class Annotation:
    """注解条目"""
    term: str
    explanation: str
    category: str  # term, history, people, concept


class NewsTranslator:
    """新闻翻译器"""
    
    def __init__(self):
        # 专业术语词典
        self.term_dict = self._load_term_dict()
    
    def _load_term_dict(self) -> Dict[str, str]:
        """加载专业术语词典"""
        return {
            # 科技/AI
            "LLM": "大语言模型 (Large Language Model)，如GPT、Claude等",
            "GPU": "图形处理器 (Graphics Processing Unit)，AI训练的核心硬件",
            "neural network": "神经网络，模拟人脑结构的计算模型",
            "machine learning": "机器学习，让计算机从数据中学习的技术",
            "semiconductor": "半导体，芯片的基础材料",
            "chip": "芯片/集成电路",
            
            # 财经
            "Federal Reserve": "美联储，美国中央银行",
            "inflation": "通货膨胀，货币购买力下降",
            "ETF": "交易所交易基金 (Exchange Traded Fund)",
            "cryptocurrency": "加密货币，如比特币、以太坊",
            "bull market": "牛市，股市上涨趋势",
            "bear market": "熊市，股市下跌趋势",
            
            # 时政
            "sanctions": "制裁，经济或政治惩罚措施",
            "diplomacy": "外交，国家间的谈判与关系处理",
            "NATO": "北约 (North Atlantic Treaty Organization)",
            "G7": "七国集团 (美、英、法、德、日、意、加)",
            "OPEC": "石油输出国组织",
            "trade war": "贸易战，国家间的关税对抗",
            
            # 机器人/减速器
            "RV reducer": "RV减速器，精密减速装置，用于工业机器人",
            "harmonic drive": "谐波减速器，另一种精密减速装置",
            "humanoid robot": "人形机器人，如特斯拉Optimus",
            "actuator": "执行器，驱动机器人运动的装置",
            "servo motor": "伺服电机，精密控制电机",
            "torque": "扭矩，旋转力的度量",
            
            # 马斯克相关
            "SpaceX": "太空探索技术公司，马斯克创立的航天公司",
            "Tesla": "特斯拉，电动汽车和清洁能源公司",
            "Neuralink": "脑机接口公司，研发植入式脑芯片",
            "The Boring Company": "无聊公司，隧道挖掘和基础设施公司",
            "DOGE": "狗狗币 (Dogecoin)，一种加密货币",
            "Grok": "马斯克旗下xAI开发的AI聊天机器人",
            "Optimus": "擎天柱，特斯拉开发的人形机器人",
            
            # Skills / MCP / CLI 生态
            "MCP": "Model Context Protocol，Anthropic 提出的开放协议，让 AI 助手能安全地调用外部工具和数据库",
            "Model Context Protocol": "模型上下文协议，AI 代理与外部系统交互的标准接口",
            "skill": "技能包/插件，为 AI 代理扩展特定能力的模块化组件",
            "CLI": "Command Line Interface，命令行界面，通过文本指令与软件交互的方式",
            "plugin": "插件，为主程序增加功能的扩展模块",
            "extension": "浏览器或编辑器的扩展程序",
            "agent": "AI 代理/智能体，能自主执行任务的 AI 程序",
            "workflow": "工作流，一系列自动化执行的任务步骤",
            "GitHub": "全球最大的代码托管平台，开源项目的主要聚集地",
            "Hacker News": "Y Combinator 旗下的科技新闻社区，硅谷开发者必看",
            "Reddit": "美国最大的论坛社区，拥有众多技术讨论版块 (subreddit)",
        }
    
    def translate_text(self, text: str) -> str:
        """
        单条翻译（兼容旧接口）
        优先 DeepSeek，无 key 时回退 MyMemory
        """
        if not text or not text.strip():
            return text
        from deepseek_translator import translate_with_deepseek
        return translate_with_deepseek([text])[0]
    
    def translate_batch(self, texts: List[str]) -> List[str]:
        """批量翻译，效率更高"""
        from deepseek_translator import translate_with_deepseek
        return translate_with_deepseek(texts)
    
    def extract_terms_for_annotation(self, title: str, summary: str) -> List[Annotation]:
        """从新闻中提取需要注解的术语"""
        annotations = []
        full_text = (title + " " + summary).lower()
        
        for term, explanation in self.term_dict.items():
            if term.lower() in full_text:
                annotations.append(Annotation(
                    term=term,
                    explanation=explanation,
                    category="term"
                ))
        
        # 检查人名
        people_patterns = [
            (r'\bMusk\b', '埃隆·马斯克 (Elon Musk)，特斯拉、SpaceX、X(推特) 等公司的CEO'),
            (r'\bTrump\b', '唐纳德·特朗普 (Donald Trump)，美国前总统'),
            (r'\bBiden\b', '乔·拜登 (Joe Biden)，美国总统'),
            (r'\bBezos\b', '杰夫·贝索斯 (Jeff Bezos)，亚马逊创始人'),
            (r'\bZuckerberg\b', '马克·扎克伯格 (Mark Zuckerberg)，Meta CEO'),
            (r'\bAltman\b', '山姆·奥特曼 (Sam Altman)，OpenAI CEO'),
            (r'\bNadella\b', '萨提亚·纳德拉 (Satya Nadella)，微软CEO'),
            (r'\bHuang\b', '黄仁勋 (Jensen Huang)，NVIDIA CEO'),
        ]
        
        for pattern, explanation in people_patterns:
            if re.search(pattern, title + " " + summary):
                name = pattern.replace(r'\b', '').replace(r'\b', '')
                annotations.append(Annotation(
                    term=name,
                    explanation=explanation,
                    category="people"
                ))
        
        # 去重
        seen = set()
        unique = []
        for ann in annotations:
            if ann.term not in seen:
                seen.add(ann.term)
                unique.append(ann)
        
        return unique
    
    def generate_context_annotation(self, news_item) -> List[str]:
        """
        生成上下文注解
        解释新闻的背景和历史
        """
        annotations = []
        title_lower = news_item.title.lower()
        
        # 中美贸易战背景
        if any(k in title_lower for k in ['us china', 'trade war', 'sanctions', 'tariff']):
            annotations.append(
                "📚 背景知识：中美贸易争端始于2018年，美国对中国商品加征关税，"
                "中国采取反制措施。这场争端影响全球供应链和科技产业格局。"
            )
        
        # AI监管背景
        if any(k in title_lower for k in ['ai regulation', 'ai safety', 'chatgpt ban']):
            annotations.append(
                "📚 背景知识：随着ChatGPT等大模型兴起，各国开始制定AI监管政策。"
                "欧盟通过《AI法案》，美国发布AI安全框架，中国也有生成式AI管理办法。"
            )
        
        # 美联储背景
        if 'federal reserve' in title_lower or 'fed rate' in title_lower:
            annotations.append(
                "📚 背景知识：美联储通过调整利率控制通胀和就业。"
                "2022-2023年激进加息对抗通胀，2024年可能转向降息周期。"
            )
        
        # 特斯拉/电动车背景
        if 'tesla' in title_lower or 'ev market' in title_lower:
            annotations.append(
                "📚 背景知识：特斯拉是全球电动车领导者，但面临比亚迪等中国品牌的激烈竞争。"
                "电动车市场正从政策驱动转向市场驱动。"
            )
        
        # 芯片/半导体背景
        if any(k in title_lower for k in ['chip', 'semiconductor', 'nvidia']):
            annotations.append(
                "📚 背景知识：芯片是现代科技的基础。美国限制对华出口高端芯片，"
                "促使中国加速芯片自主研发。NVIDIA主导AI芯片市场。"
            )
        
        # 加密货币背景
        if any(k in title_lower for k in ['bitcoin', 'crypto', 'dogecoin']):
            annotations.append(
                "📚 背景知识：加密货币价格波动极大。2024年美国批准比特币ETF，"
                "机构资金入场。马斯克曾多次在推特提及狗狗币，引发价格剧烈波动。"
            )
        
        return annotations


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, translator: NewsTranslator):
        self.translator = translator
    
    def process_news(self, news_items: List) -> List:
        """处理新闻：批量翻译+注解"""
        if not news_items:
            return news_items
        
        # 批量收集需要翻译的文本
        titles = [item.title for item in news_items]
        # 优先翻译 full_content，否则 fallback 到 summary
        contents = [item.full_content if item.full_content else item.summary for item in news_items]
        
        # 批量翻译
        translated_titles = self.translator.translate_batch(titles)
        translated_contents = self.translator.translate_batch(contents)
        
        for i, item in enumerate(news_items):
            item.translated_title = translated_titles[i]
            item.translated_summary = translated_contents[i]
            
            # 提取术语注解（基于原文，术语库是英文的）
            text_for_terms = item.full_content if item.full_content else item.summary
            terms = self.translator.extract_terms_for_annotation(item.title, text_for_terms)
            item.annotations = [f"📖 **{a.term}**: {a.explanation}" for a in terms]
            
            # 添加上下文注解
            context = self.translator.generate_context_annotation(item)
            item.annotations.extend(context)
        
        return news_items
    
    def generate_markdown_report(self, all_news: Dict[str, List], 
                                  elon_tweets: List[Dict],
                                  is_morning: bool = True) -> str:
        """生成Markdown格式报告"""
        now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        period = "早间" if is_morning else "晚间"
        
        lines = [
            f"# 📰 全球新闻简报 - {period}版 ({now})",
            "",
            "---",
            ""
        ]
        
        # Translate Elon tweets
        if elon_tweets:
            tweet_texts = [t.get('text', '') for t in elon_tweets[:10]]
            translated_tweets = self.translator.translate_batch(tweet_texts)
            for i, tweet in enumerate(elon_tweets[:10]):
                tweet['_translated'] = translated_tweets[i]
        
        # Elon Musk tweets (priority)
        lines.extend([
            "## 马斯克动态",
            ""
        ])
        
        if elon_tweets:
            for tweet in elon_tweets[:10]:
                created = tweet.get('created_at', '')
                text = tweet.get('_translated', '') or tweet.get('text', '')
                url = tweet.get('url', '')
                likes = tweet.get('likes', 0)
                retweets = tweet.get('retweets', 0)
                
                lines.extend([
                    f"**{created}**",
                    f"> {text}",
                    f"  点赞: {likes} | 转发: {retweets}",
                ])
                if url:
                    lines.append(f"  [View on X]({url})")
                lines.append("")
        else:
            lines.extend([
                "*No updates in the last 6 hours*",
                ""
            ])
        
        lines.append("---\n")
        
        # 各分类新闻
        for category, items in all_news.items():
            if not items:
                continue
            
            lines.extend([
                f"## 📂 {category}",
                ""
            ])
            
            for i, item in enumerate(items, 1):
                title = item.translated_title or item.title
                # 优先使用完整正文，否则 fallback 到摘要
                content = item.translated_summary or item.summary
                if item.full_content and not item.translated_summary:
                    content = item.full_content
                
                lines.extend([
                    f"### {i}. {title}",
                    f"*{item.source}* | {item.published.strftime('%H:%M')}",
                    "",
                ])
                
                # 显示内容：如果很长，展示前 6000 字符并提示阅读原文
                max_display = 6000
                if len(content) > max_display:
                    lines.append(content[:max_display] + "\n\n...[内容较长，剩余部分请点击阅读原文查看]")
                else:
                    lines.append(content)
                lines.append("")
                
                # 添加注解
                if item.annotations:
                    lines.extend([
                        "**💡 知识点**:",
                        ""
                    ])
                    for ann in item.annotations:
                        lines.append(f"- {ann}")
                    lines.append("")
                
                lines.append(f"[阅读原文]({item.link})")
                lines.append("")
            
            lines.append("---\n")
        
        lines.extend([
            "",
            "*本报告由 AI 新闻秘书自动生成*",
            f"*生成时间: {now}*"
        ])
        
        return "\n".join(lines)


# 为了消除循环导入，在这里导入datetime
from datetime import datetime
