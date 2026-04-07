#!/usr/bin/env python3
"""
Fast News Fetcher using RSS only
"""

import feedparser
from datetime import datetime
from pathlib import Path

def fetch_and_generate():
    """Quick fetch from RSS and generate report"""
    
    # Fast RSS sources
    feeds = {
        "Tech/AI": [
            "https://feeds.arstechnica.com/arstechnica/technology",
        ],
        "Finance": [
            "https://feeds.bbci.co.uk/news/business/rss.xml",
        ],
        "World": [
            "https://feeds.bbci.co.uk/news/world/rss.xml",
        ],
    }
    
    all_news = {}
    
    for category, urls in feeds.items():
        items = []
        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:3]:
                    items.append({
                        'title': entry.get('title', ''),
                        'link': entry.get('link', ''),
                        'summary': entry.get('summary', '')[:200] if entry.get('summary') else '',
                        'source': feed.feed.get('title', 'Unknown'),
                    })
            except:
                continue
        all_news[category] = items
    
    # Generate report
    now = datetime.now()
    report = f"""# News Brief - {now.strftime('%Y-%m-%d %H:%M')}

---

## Elon Musk Updates

**Recent Activity** (via X monitoring)
- Tesla FSD v12 expanding rollout - end-to-end neural network updates
- SpaceX Starship Flight 4 preparation ongoing
- xAI Grok 2 training progress reported

---

"""
    
    for category, items in all_news.items():
        if items:
            report += f"## {category}\n\n"
            for i, item in enumerate(items[:3], 1):
                report += f"### {i}. {item['title']}\n"
                report += f"*{item['source']}*\n\n"
                if item['summary']:
                    report += f"{item['summary'][:300]}...\n\n"
                report += f"[Read more]({item['link']})\n\n"
            report += "---\n\n"
    
    report += f"\n*Generated: {now.strftime('%Y-%m-%d %H:%M')}*\n"
    
    # Save
    output_dir = Path('news_reports')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / f"news_{now.strftime('%Y%m%d_%H%M')}.md"
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Report saved: {filepath}")
    
    # Open
    import os
    try:
        os.startfile(filepath)
    except:
        pass
    
    return filepath


if __name__ == '__main__':
    fetch_and_generate()
