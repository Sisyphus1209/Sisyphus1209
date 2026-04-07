#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Elon Musk Tweet Scraper - Real-time fetcher
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict
import re


class ElonScraper:
    """Scrape Elon Musk's tweets from Nitter"""
    
    def __init__(self):
        self.nitter_instances = [
            "https://nitter.net",
            "https://nitter.it",
            "https://nitter.cz",
        ]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_tweets(self, max_tweets: int = 10) -> List[Dict]:
        """Fetch tweets from Nitter"""
        tweets = []
        
        for instance in self.nitter_instances:
            try:
                url = f"{instance}/elonmusk"
                print(f"Trying {instance}...")
                
                response = self.session.get(url, timeout=15)
                if response.status_code != 200:
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find tweet containers
                tweet_divs = soup.find_all('div', class_='timeline-item')
                
                for div in tweet_divs[:max_tweets]:
                    try:
                        # Get tweet text
                        content_div = div.find('div', class_='tweet-content')
                        if not content_div:
                            continue
                        
                        text_div = content_div.find('div', class_='tweet-body')
                        if not text_div:
                            continue
                        
                        # Extract text
                        text_elem = text_div.find('div', class_='tweet-text')
                        text = text_elem.get_text(strip=True) if text_elem else ""
                        
                        # Clean up text
                        text = re.sub(r'\s+', ' ', text).strip()
                        
                        if len(text) < 10:
                            continue
                        
                        # Get time
                        time_elem = div.find('span', class_='tweet-date')
                        time_str = ""
                        if time_elem and time_elem.find('a'):
                            time_str = time_elem.find('a').get_text(strip=True)
                        
                        # Get stats
                        stats = div.find('div', class_='tweet-stats')
                        likes = retweets = replies = 0
                        
                        if stats:
                            stat_spans = stats.find_all('span', class_='tweet-stat')
                            for span in stat_spans:
                                icon = span.find('div', class_='icon')
                                if icon:
                                    icon_class = icon.get('class', [])
                                    count_elem = span.find('div', class_='icon-text')
                                    count = count_elem.get_text(strip=True) if count_elem else "0"
                                    
                                    if 'heart' in str(icon_class):
                                        likes = self._parse_count(count)
                                    elif 'retweet' in str(icon_class):
                                        retweets = self._parse_count(count)
                                    elif 'comment' in str(icon_class):
                                        replies = self._parse_count(count)
                        
                        tweet = {
                            'text': text,
                            'created_at': time_str or datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'source': 'X/Twitter',
                            'url': 'https://twitter.com/elonmusk',
                            'likes': likes,
                            'retweets': retweets,
                            'replies': replies
                        }
                        tweets.append(tweet)
                        
                    except Exception as e:
                        continue
                
                if tweets:
                    print(f"Successfully fetched {len(tweets)} tweets from {instance}")
                    return tweets
                    
            except Exception as e:
                print(f"Failed {instance}: {e}")
                continue
        
        return tweets
    
    def _parse_count(self, count_str: str) -> int:
        """Parse count string like '1.2K' to number"""
        try:
            count_str = count_str.strip().replace(',', '')
            if 'K' in count_str:
                return int(float(count_str.replace('K', '')) * 1000)
            elif 'M' in count_str:
                return int(float(count_str.replace('M', '')) * 1000000)
            else:
                return int(count_str) if count_str else 0
        except:
            return 0


if __name__ == '__main__':
    scraper = ElonScraper()
    tweets = scraper.fetch_tweets(5)
    
    print(f"\n{'='*60}")
    print(f"Fetched {len(tweets)} tweets")
    print(f"{'='*60}\n")
    
    for i, tweet in enumerate(tweets, 1):
        print(f"{i}. [{tweet['created_at']}]")
        print(f"   {tweet['text'][:100]}...")
        print(f"   Likes: {tweet['likes']} | RT: {tweet['retweets']}")
        print()
