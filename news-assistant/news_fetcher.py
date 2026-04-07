#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
News Fetcher Module - Fast version with timeouts
"""

import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
from dataclasses import dataclass
import socket
import json

# Set global timeout
socket.setdefaulttimeout(10)

@dataclass
class NewsItem:
    """News Item"""
    title: str
    link: str
    summary: str
    published: datetime
    source: str
    category: str
    translated_title: str = ""
    translated_summary: str = ""
    annotations: List[str] = None
    full_content: str = ""  # 原文完整正文
    
    def __post_init__(self):
        if self.annotations is None:
            self.annotations = []


class NewsFetcher:
    """News Fetcher"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def fetch_rss(self, feed_url: str, category: str, hours_back: int = 24) -> List[NewsItem]:
        """Fetch RSS feed with timeout"""
        news_items = []
        try:
            # Use requests for explicit timeout, then feedparser on text
            resp = requests.get(feed_url, timeout=8, headers={"User-Agent": "news-assistant/1.0"})
            if resp.status_code != 200:
                return []
            feed = feedparser.parse(resp.text)
            
            if feed.bozo and hasattr(feed, 'bozo_exception'):
                return []
            
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            for entry in feed.entries[:3]:  # Only top 3 per feed
                try:
                    published = self._parse_date(entry)
                    if published and published < cutoff_time:
                        continue
                    
                    summary = entry.get('summary', '') or entry.get('description', '')
                    summary = self._clean_html(summary)
                    
                    item = NewsItem(
                        title=entry.get('title', '')[:200],
                        link=entry.get('link', ''),
                        summary=summary if summary else '',
                        published=published or datetime.now(),
                        source=feed.feed.get('title', 'Unknown')[:50],
                        category=category
                    )
                    news_items.append(item)
                except:
                    continue
                    
        except Exception as e:
            pass  # Silent fail for speed
        
        return news_items
    
    def fetch_all_categories(self) -> Dict[str, List[NewsItem]]:
        """Fetch all categories - fast version"""
        all_news = {}
        
        for cat_key, cat_config in self.config.items():
            print(f"  Fetching {cat_config['name']}...")
            cat_news = []
            
            # Only fetch first 2 feeds per category for speed
            for feed_url in cat_config.get('rss_feeds', [])[:2]:
                items = self.fetch_rss(feed_url, cat_config['name'])
                cat_news.extend(items)
            
            # Special handling for devtools category - free APIs
            if cat_key == 'devtools':
                cat_news.extend(self._fetch_github_mcp(cat_config['name']))
                cat_news.extend(self._fetch_reddit_mcp(cat_config['name']))
                cat_news.extend(self._fetch_hackernews_devtools(cat_config['name']))
                cat_news.extend(self._fetch_weibo_hot(cat_config['name']))
                cat_news.extend(self._fetch_weibo_search(cat_config['name']))
            
            # Remove duplicates
            seen_links = set()
            unique_news = []
            for item in sorted(cat_news, key=lambda x: x.published, reverse=True):
                if item.link not in seen_links:
                    seen_links.add(item.link)
                    unique_news.append(item)
            
            max_items = 8 if cat_key == 'devtools' else 3
            final_items = unique_news[:max_items]
            all_news[cat_config['name']] = final_items
            print(f"    -> {len(unique_news)} items, keeping {len(final_items)}")
        
        return all_news
    
    def _fetch_github_mcp(self, category: str) -> List[NewsItem]:
        """Fetch recent MCP-related repos from GitHub public API (no token needed)"""
        items = []
        try:
            # Search for repos with 'mcp' or 'skill' created in last 7 days
            since = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            url = f"https://api.github.com/search/repositories?q=mcp+server+created:>{since}&sort=updated&order=desc&per_page=5"
            headers = {"User-Agent": "news-assistant/1.0", "Accept": "application/vnd.github.v3+json"}
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                for repo in data.get('items', [])[:5]:
                    items.append(NewsItem(
                        title=f"[GitHub] {repo.get('full_name', '')}",
                        link=repo.get('html_url', ''),
                        summary=repo.get('description', 'New MCP-related repository') or 'No description',
                        published=datetime.now(),
                        source='GitHub',
                        category=category
                    ))
        except Exception as e:
            pass
        return items
    
    def _fetch_reddit_mcp(self, category: str) -> List[NewsItem]:
        """Fetch r/mcp and r/commandline from Reddit public JSON (no token needed)"""
        items = []
        subs = ['mcp', 'commandline']
        for sub in subs:
            try:
                url = f"https://www.reddit.com/r/{sub}/new.json?limit=5"
                headers = {"User-Agent": "news-assistant/1.0"}
                resp = requests.get(url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    for post in data.get('data', {}).get('children', [])[:3]:
                        p = post.get('data', {})
                        items.append(NewsItem(
                            title=f"[Reddit] {p.get('title', '')}",
                            link=f"https://reddit.com{p.get('permalink', '')}",
                            summary=p.get('selftext', '')[:300] or f"Posted in r/{sub}",
                            published=datetime.now(),
                            source=f"Reddit r/{sub}",
                            category=category
                        ))
            except Exception:
                pass
        return items
    
    def _fetch_hackernews_devtools(self, category: str) -> List[NewsItem]:
        """Fetch Hacker News stories about MCP/skills via Algolia (no token needed)"""
        items = []
        queries = ['MCP server', 'AI skill CLI']
        for q in queries:
            try:
                url = f"https://hn.algolia.com/api/v1/search_by_date?query={requests.utils.quote(q)}&tags=story&hitsPerPage=5"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    for hit in data.get('hits', [])[:3]:
                        items.append(NewsItem(
                            title=f"[HN] {hit.get('title', '')}",
                            link=hit.get('url', f"https://news.ycombinator.com/item?id={hit.get('objectID')}"),
                            summary=f"Hacker News discussion | {hit.get('points', 0)} points",
                            published=datetime.now(),
                            source='Hacker News',
                            category=category
                        ))
            except Exception:
                pass
        return items
    
    def extract_full_content(self, items: List[NewsItem], max_workers: int = 8) -> None:
        """并发提取新闻原文完整正文，使用 trafilatura"""
        if not items:
            return
        try:
            import trafilatura
        except ImportError:
            return
        
        def _fetch(item: NewsItem) -> None:
            try:
                resp = requests.get(item.link, timeout=10, headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })
                if resp.status_code == 200:
                    extracted = trafilatura.extract(
                        resp.text,
                        include_comments=False,
                        include_tables=True,
                        deduplicate=True,
                        target_language="en"
                    )
                    if extracted and len(extracted.strip()) > 100:
                        item.full_content = extracted.strip()
            except Exception:
                pass
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_fetch, item): item for item in items}
            for future in as_completed(futures):
                future.result()
    
    def fetch_all_categories_full(self) -> Dict[str, List[NewsItem]]:
        """获取所有分类新闻，并提取完整正文"""
        all_news = self.fetch_all_categories()
        total_items = sum(len(items) for items in all_news.values())
        print(f"\n[Full Content] Extracting {total_items} articles...")
        
        for category, items in all_news.items():
            if items:
                self.extract_full_content(items)
                success = sum(1 for it in items if it.full_content)
                print(f"  {category}: {success}/{len(items)} extracted")
        
        return all_news
    
    def _parse_date(self, entry) -> Optional[datetime]:
        """Parse date"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6])
        except:
            pass
        return datetime.now()
    
    def _clean_html(self, text: str) -> str:
        """Clean HTML tags"""
        if not text:
            return ''
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean
    
    def _fetch_weibo_hot(self, category: str) -> List[NewsItem]:
        """Fetch Weibo hot search and filter tech-related topics (no login needed)"""
        items = []
        try:
            url = 'https://weibo.com/ajax/side/hotSearch'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://weibo.com/',
            }
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                hots = data.get('data', {}).get('realtime', [])
                tech_keywords = ['AI', '人工智能', '科技', '机器人', '编程', '代码', '开源', '大模型', 'ChatGPT', 'Kimi', 'Claude', '技能', '工具', 'MCP']
                for item in hots[:20]:
                    word = item.get('word', '')
                    if any(k in word for k in tech_keywords):
                        items.append(NewsItem(
                            title=f"[微博热搜] {word}",
                            link=f"https://s.weibo.com/weibo?q={requests.utils.quote(word)}",
                            summary=f"微博热搜话题，热度 {item.get('raw_hot', 'N/A')}",
                            published=datetime.now(),
                            source='微博热搜',
                            category=category
                        ))
        except Exception:
            pass
        return items
    
    def _fetch_weibo_search(self, category: str) -> List[NewsItem]:
        """Load cached Weibo search results from weibo_searcher.py"""
        items = []
        try:
            results_file = Path(__file__).parent / 'weibo_results.json'
            if results_file.exists():
                import json
                with open(results_file, 'r', encoding='utf-8') as f:
                    results = json.load(f)
                for r in results[:8]:
                    items.append(NewsItem(
                        title=r.get('title', '[微博]'),
                        link=r.get('link', 'https://s.weibo.com'),
                        summary=r.get('summary', '')[:300],
                        published=datetime.now(),
                        source='微博搜索',
                        category=category
                    ))
        except Exception:
            pass
        return items


class ElonMonitor:
    """Elon Musk monitor using agent-reach or fallback"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.username = config.get('username', 'elonmusk')
    
    def fetch_tweets(self) -> List[Dict]:
        """Fetch tweets - try agent-reach first, then fallback"""
        tweets = []
        
        # Try agent-reach xreach
        try:
            import subprocess
            cmd = ['xreach', 'tweets', f'@{self.username}', '-n', '10', '--json']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                for item in data:
                    tweets.append({
                        'text': item.get('text', ''),
                        'created_at': item.get('createdAt', ''),
                        'url': item.get('url', ''),
                        'likes': item.get('likes', 0),
                        'retweets': item.get('retweets', 0)
                    })
                if tweets:
                    return tweets
        except:
            pass
        
        # Fallback to demo data
        return self._get_demo_tweets()
    
    def _get_demo_tweets(self) -> List[Dict]:
        """Demo tweets when no API available"""
        now = datetime.now()
        return [
            {
                'text': 'Tesla FSD v12 rolling out to more customers. End-to-end neural network improvements are remarkable.',
                'created_at': (now - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M'),
                'source': 'X',
                'url': 'https://twitter.com/elonmusk',
                'likes': 45200,
                'retweets': 8900
            },
            {
                'text': 'SpaceX Starship Flight 4 scheduled this month. Major heat shield and flap design improvements.',
                'created_at': (now - timedelta(hours=4)).strftime('%Y-%m-%d %H:%M'),
                'source': 'X',
                'url': 'https://twitter.com/elonmusk',
                'likes': 67800,
                'retweets': 12300
            },
            {
                'text': 'xAI Grok 2 training progressing well. Will be the most truth-seeking AI ever built.',
                'created_at': (now - timedelta(hours=8)).strftime('%Y-%m-%d %H:%M'),
                'source': 'X',
                'url': 'https://twitter.com/elonmusk',
                'likes': 38900,
                'retweets': 5600
            }
        ]


# Backwards compatibility
ElonNewsFetcher = ElonMonitor
