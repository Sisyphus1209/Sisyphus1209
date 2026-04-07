#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Elon Musk News Fetcher - Alternative implementation
Uses web search to find recent Elon Musk news/tweets
"""

import subprocess
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict


class ElonNewsFetcher:
    """Fetch Elon Musk news from web search"""
    
    def __init__(self):
        self.cache_file = ".elon_cache.json"
        self.cache_duration = timedelta(minutes=30)
    
    def fetch_recent_news(self) -> List[Dict]:
        """Fetch recent Elon Musk news"""
        # Try to use curl with jina.ai summarizer
        try:
            # Search for recent Elon news
            search_urls = [
                "https://r.jina.ai/https://twitter.com/elonmusk",
                "https://r.jina.ai/https://www.google.com/search?q=elon+musk+latest+news+today",
            ]
            
            results = []
            for url in search_urls:
                try:
                    cmd = ['curl', '-s', '-L', '--max-time', '15', url]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
                    if result.returncode == 0:
                        content = result.stdout[:3000]  # Limit content
                        # Extract potential tweet-like content
                        lines = content.split('\n')
                        for line in lines:
                            line = line.strip()
                            if len(line) > 20 and len(line) < 500:
                                # Looks like a tweet or news snippet
                                if any(kw in line.lower() for kw in ['elon', 'musk', 'tesla', 'spacex', 'x', '@']):
                                    results.append({
                                        'text': line,
                                        'source': 'Web',
                                        'time': datetime.now().strftime('%Y-%m-%d %H:%M')
                                    })
                except:
                    continue
            
            return results[:10]  # Return top 10
            
        except Exception as e:
            print(f"Error fetching Elon news: {e}")
            return []
    
    def fetch_from_nitter(self) -> List[Dict]:
        """Try to fetch from Nitter (Twitter alternative)"""
        try:
            nitter_instances = [
                "https://nitter.net/elonmusk",
                "https://nitter.it/elonmusk",
            ]
            
            for url in nitter_instances:
                try:
                    cmd = ['curl', '-s', '-L', '--max-time', '10', url]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                    
                    if result.returncode == 0 and 'tweet-content' in result.stdout:
                        # Parse tweets from HTML
                        html = result.stdout
                        tweets = []
                        
                        # Simple regex extraction
                        content_matches = re.findall(r'class="tweet-content[^"]*"[^>]*>([^<]+)', html)
                        time_matches = re.findall(r'class="tweet-date"[^>]*>[^<]*<[^>]*>([^<]+)', html)
                        
                        for i, content in enumerate(content_matches[:5]):
                            content = re.sub(r'<[^>]+>', '', content).strip()
                            time_str = time_matches[i] if i < len(time_matches) else 'Recent'
                            
                            if len(content) > 10:
                                tweets.append({
                                    'text': content,
                                    'created_at': time_str,
                                    'source': 'X/Twitter',
                                    'url': f'https://twitter.com/elonmusk'
                                })
                        
                        if tweets:
                            return tweets
                            
                except:
                    continue
                    
        except Exception as e:
            print(f"Nitter fetch error: {e}")
        
        return []
    
    def get_mock_tweets(self) -> List[Dict]:
        """Return mock tweets for demonstration"""
        return [
            {
                'text': 'Tesla FSD v12 is rolling out to more customers. The improvement in end-to-end neural networks is remarkable.',
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
                'source': 'X/Twitter (Demo)',
                'url': 'https://twitter.com/elonmusk',
                'likes': 45200,
                'retweets': 8900
            },
            {
                'text': 'SpaceX Starship flight 4 scheduled soon. Major improvements to heat shield and flap design.',
                'created_at': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M'),
                'source': 'X/Twitter (Demo)',
                'url': 'https://twitter.com/elonmusk',
                'likes': 67800,
                'retweets': 12300
            },
            {
                'text': 'xAI Grok 2 training underway. Will be the most truth-seeking AI ever built.',
                'created_at': (datetime.now() - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M'),
                'source': 'X/Twitter (Demo)',
                'url': 'https://twitter.com/elonmusk',
                'likes': 38900,
                'retweets': 5600
            }
        ]
    
    def fetch_all(self) -> List[Dict]:
        """Fetch all Elon updates"""
        # Try real sources first
        tweets = self.fetch_from_nitter()
        
        if not tweets:
            tweets = self.fetch_recent_news()
        
        # Fall back to mock data for demo
        if not tweets:
            print("    Using demo data (set up agent-reach for real data)")
            tweets = self.get_mock_tweets()
        
        return tweets


# For backwards compatibility
ElonMonitor = ElonNewsFetcher
