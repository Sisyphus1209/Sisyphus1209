#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply manual/Kimi translation to a generated report.
Run this after Kimi has provided the translations.
"""

from pathlib import Path
import sys


def apply_translation(report_path: str):
    path = Path(report_path)
    text = path.read_text(encoding='utf-8')
    
    # ========== TITLES ==========
    title_map = {
        "Is the Slate Truck too minimal for its own good?": "Slate Truck 是不是太过简约了？",
        "How the Amazon Echo learned to talk — and listen": "亚马逊 Echo 是如何学会说话——并倾听的",
        "Grammarly’s sloppelganger saga": "Grammarly 的\"山寨版\"风波",
        "‘Our mood changes almost on a daily basis’: Why $4 gas prices feel a lot worse this time around": "\"我们的心情几乎每天都在变化\"：为什么这次4美元的油价让人感觉糟得多",
        "‘This is an overlooked catastrophe’: Why do so many hospitals not accept Medicare Advantage for cancer patients?": "\"这是一场被忽视的灾难\"：为什么这么多医院不接受癌症患者的医疗保险优势计划？",
        "‘We’re aiming for a monthly income of $11,500’: I’m 64. I’ve $1.5 million in a 401(k). How do I time my withdrawals?": "\"我们的目标是每月收入11,500美元\"：我今年64岁，401(k)账户里有150万美元。我该如何把握取款时机？",
        "These rock-climbing fish can shimmy up a 50-foot waterfall": "这些攀岩鱼能爬上50英尺高的瀑布",
        "In Lebanon, more than 50 medics have been killed by Israel. Some say they're targeted": "在黎巴嫩，超过50名医护人员被以色列杀害。有人说他们是被蓄意攻击的目标",
        "Questions to help you get 'financially naked' with your partner": "帮助你与伴侣\"财务赤裸相待\"的问题",
        "[HN] My 11-step GraphRAG pipeline, what worked, and what's still broken": "[HN] 我的11步 GraphRAG 流程：什么有效，什么还有问题",
        "[HN] Is MCP Dead? What We Learned on MCP, CLI, and Skills": "[HN] MCP 已死？我们在 MCP、CLI 和 Skills 上的经验教训",
        "[HN] Web3 project technical analysis Skill for AI agents": "[HN] 面向 AI 代理的 Web3 项目技术分析 Skill",
        "[HN] We Score MCP Servers — and Why We Rebuilt It from Scratch": "[HN] 我们给 MCP 服务器打分——以及为什么我们要从头重建",
        "[HN] 17,000 MCP Servers — and the Security Threats Nobody Is Talking About": "[HN] 17,000 个 MCP 服务器——以及没人谈论的安全威胁",
        "[HN] MCP Shield — Audit MCP servers for supply chain attacks before installing them": "[HN] MCP Shield——安装前审计 MCP 服务器的供应链攻击风险",
        "[GitHub] ColonistOne/thecolony-mcp-server": "[GitHub] ColonistOne/thecolony-mcp-server",
        "[GitHub] ritw237/job-search-mcp": "[GitHub] ritw237/job-search-mcp",
    }
    
    # ========== SUMMARIES ==========
    summary_map = {
        "The first thing you notice about the Slate Truck is its size. It's small, surprisingly so. In a country where trucks often come with their own zip code, Slate's pickup is refreshingly puny, measuring 174.6 inches long, 70.6 inches wide, and 69.3 inches tall, with a curb weight of approximately 3,602": "关于 Slate Truck，你首先注意到的是它的尺寸。它很小，小到令人惊讶。在一个卡车往往自带邮编的国家，Slate 的皮卡显得格外娇小，长174.6英寸、宽70.6英寸、高69.3英寸，整备质量约3,602磅。",
        "Jeff Bezos badly wanted a voice computer. He had been saying so publicly since the very early days of Amazon, telling anyone who would listen about why voice might make it easier and more natural to interact with technology. (And to buy stuff from Jeff Bezos.) But when a team at Amazon set out to [": "杰夫·贝索斯非常想要一台语音电脑。从亚马逊创立之初，他就公开表达这一想法，向任何愿意倾听的人解释语音为何能让人与科技的互动更轻松自然。（以及更方便从杰夫·贝索斯那里买东西。）但当亚马逊的一个团队开始着手...",
        "This is The Stepback, a weekly newsletter breaking down one essential story from the tech world. For more on the ups and downs of AI, follow Stevie Bonifield. The Stepback arrives in our subscribers' inboxes at 8AM ET. Opt in for The Stepback here. How it started Most people probably know Grammarly": "这是 The Stepback，一份每周 newsletter，深度解析科技界的一个重要故事。想了解更多 AI 的起起落落，请关注 Stevie Bonifield。The Stepback 每周美东时间早上8点送达订阅者邮箱。点击此处订阅 The Stepback。故事起源：大多数人可能都知道 Grammarly...",
        "As far as gas prices go, there is no hive mind.": "就油价而言，并不存在集体共识。",
        "\"Insurers have pushed certain cancer-care centers out of network before the end of the calendar or policy year.\"": "\"保险公司已在日历年度或保单年度结束前，将某些癌症护理中心排除在合作网络之外。\"",
        "\"I plan to start collecting my Social Security of $4,100 at 68.\"": "\"我计划在68岁时开始领取每月4,100美元的社会保障金。\"",
        "New research from the Democratic Republic of Congo offers a behavioral and anatomical portrait of a species that can achieve surprising athletic feats.": "来自刚果民主共和国的一项新研究，从行为和解剖学角度描绘了一种能够完成惊人运动壮举的物种。",
        "Lebanon says at least 54 health workers are among more than 1,400 people killed by Israel during the current invasion. Human rights groups say first responders are being targeted — something Israel denies.": "黎巴嫩称，在当前以色列的入侵行动中，至少有54名医护人员在超过1,400名遇难者之列。人权组织表示急救人员正成为攻击目标——以色列对此予以否认。",
        "Having \"brutally honest conversations\" about money can bring couples closer together, says Vivian Tu, a financial educator. She shares questions to ask your partner at every relationship stage.": "理财教育家 Vivian Tu 表示，关于金钱\"残酷而坦诚的对话\"能让伴侣关系更亲密。她分享了在每个关系阶段都应该问伴侣的问题。",
        "Hacker News discussion | 3 points": "Hacker News 讨论 | 3 赞",
        "Hacker News discussion | 4 points": "Hacker News 讨论 | 4 赞",
        "Hacker News discussion | 1 points": "Hacker News 讨论 | 1 赞",
        "MCP server for The Colony (thecolony.cc) — collaborative intelligence platform where AI agents and humans share findings, discuss ideas, and build knowledge together. 7 MCP tools.": "面向 The Colony (thecolony.cc) 的 MCP 服务器——一个协作智能平台，AI 代理与人类在此分享发现、讨论想法、共同构建知识。包含 7 个 MCP 工具。",
        "MCP server for searching remote jobs across 100K+ listings": "面向 10万+ 职位列表的远程工作搜索 MCP 服务器",
    }
    
    # ========== ELON TWEETS ==========
    tweet_map = {
        "Tesla FSD v12 rolling out to more customers. End-to-end neural network improvements are remarkable.": "特斯拉 FSD v12 正在向更多客户推送。端到端神经网络的改进令人瞩目。",
        "SpaceX Starship Flight 4 scheduled this month. Major heat shield and flap design improvements.": "SpaceX 星舰第四次试飞定于本月进行。热盾和襟翼设计有重大改进。",
        "xAI Grok 2 training progressing well. Will be the most truth-seeking AI ever built.": "xAI Grok 2 的训练进展顺利。将成为有史以来最追求真相的 AI。",
    }
    
    # Apply replacements
    for en, zh in title_map.items():
        text = text.replace(f"### {i}. {en}" if False else f"### ", f"###TEMP###")  # dummy, will do exact below
        text = text.replace(en, zh)
    
    for en, zh in summary_map.items():
        text = text.replace(en, zh)
    
    for en, zh in tweet_map.items():
        text = text.replace(f"> {en}", f"> {zh}")
    
    # Also translate section header
    text = text.replace("## Elon Musk Updates", "## 马斯克动态")
    
    path.write_text(text, encoding='utf-8')
    print(f"[OK] Translation applied: {path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default to latest report
        reports_dir = Path(__file__).parent / "news_reports"
        reports = sorted(reports_dir.glob("news_morning_*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        if reports:
            target = reports[0]
        else:
            print("No report found.")
            sys.exit(1)
    else:
        target = sys.argv[1]
    
    apply_translation(target)
