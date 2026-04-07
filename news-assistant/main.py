#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
News Assistant Main
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import NEWS_CATEGORIES, ELON_CONFIG, PUSH_CONFIG, OUTPUT_CONFIG
from news_fetcher import NewsFetcher, ElonMonitor
from translator import NewsTranslator, ReportGenerator
from memory_client import NewsMemory


class NewsAssistant:
    """News Assistant"""
    
    def __init__(self, fast_mode: bool = False):
        self.fetcher = NewsFetcher(NEWS_CATEGORIES)
        self.elon_monitor = ElonMonitor(ELON_CONFIG)
        self.translator = NewsTranslator()
        self.generator = ReportGenerator(self.translator)
        self.output_dir = Path(OUTPUT_CONFIG['output_dir'])
        self.output_dir.mkdir(exist_ok=True)
        self.memory = NewsMemory()
        self.fast_mode = fast_mode
        
        self.last_push_file = self.output_dir / ".last_push"
        self.last_push = self._load_last_push()
        
        if self.memory.is_ready():
            prefs = self.memory.load_preferences()
            if prefs.get("favorite_categories"):
                print(f"[Memory] Favorite categories loaded: {len(prefs['favorite_categories'])}")
    
    def _load_last_push(self) -> dict:
        """Load last push record"""
        if self.last_push_file.exists():
            try:
                with open(self.last_push_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"morning": None, "evening": None}
    
    def _save_last_push(self):
        """Save push record"""
        with open(self.last_push_file, 'w', encoding='utf-8') as f:
            json.dump(self.last_push, f)
    
    def run_once(self, force: bool = False, is_morning: bool = True) -> str:
        """Run once"""
        period = "Morning" if is_morning else "Evening"
        print(f"\n{'='*60}")
        print(f"[News Assistant] Starting - {period} Edition")
        print(f"{'='*60}\n")
        
        # 0. Memory hint
        if self.memory.is_ready():
            recent = self.memory.recall_recent_reports(limit=3)
            if recent:
                print(f"[Memory] Recent runs: {len(recent)}")
        
        # 1. Fetch news
        print("[1/4] Fetching global news...")
        try:
            if self.fast_mode:
                all_news = self.fetcher.fetch_all_categories()
            else:
                all_news = self.fetcher.fetch_all_categories_full()
            total = sum(len(items) for items in all_news.values())
            print(f"      Total: {total} items")
        except Exception as e:
            print(f"      Error: {e}")
            all_news = {}
        
        # 2. Monitor Elon
        print("[2/4] Monitoring Elon Musk...")
        try:
            elon_tweets = self.elon_monitor.fetch_tweets()
            print(f"      Got {len(elon_tweets)} tweets")
        except Exception as e:
            print(f"      Error: {e}")
            elon_tweets = []
        
        # 3. Process
        print("[3/4] Processing...")
        for category, items in all_news.items():
            if items:
                try:
                    self.generator.process_news(items)
                    print(f"      {category}: {len(items)} processed")
                except Exception as e:
                    print(f"      Error processing {category}: {e}")
        
        # 4. Generate report
        print("[4/4] Generating report...")
        try:
            report = self.generator.generate_markdown_report(
                all_news, elon_tweets, is_morning
            )
        except Exception as e:
            print(f"      Error generating report: {e}")
            report = f"# Error\n\nFailed to generate report: {e}"
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        period_code = "morning" if is_morning else "evening"
        filename = f"news_{period_code}_{timestamp}.md"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n[OK] Report saved: {filepath}")
        
        # Update record
        today = datetime.now().strftime("%Y-%m-%d")
        if is_morning:
            self.last_push["morning"] = today
        else:
            self.last_push["evening"] = today
        self._save_last_push()
        
        # Memory: save run
        if self.memory.is_ready():
            self.memory.save_run(str(filepath), list(all_news.keys()))
            # Track interesting devtools
            devtools = all_news.get("Skills / MCP / CLI 生态", [])
            for item in devtools[:3]:
                if "GitHub" in item.source or "Reddit" in item.source or "Hacker News" in item.source:
                    self.memory.track_tool(item.title.replace("[GitHub] ", "").replace("[Reddit] ", "").replace("[HN] ", ""), "tool", item.link)
        
        # Open report
        try:
            os.startfile(filepath)
        except:
            pass
        
        return str(filepath)
    
    def check_and_push(self):
        """Check and push"""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        
        # Check morning
        if current_time >= PUSH_CONFIG['morning_time'] and self.last_push.get("morning") != today:
            print(f"[{current_time}] Trigger Morning push...")
            self.run_once(is_morning=True)
            return
        
        # Check evening
        if current_time >= PUSH_CONFIG['evening_time'] and self.last_push.get("evening") != today:
            print(f"[{current_time}] Trigger Evening push...")
            self.run_once(is_morning=False)
            return
        
        print(f"[{current_time}] No push scheduled")
    
    def run_scheduler(self):
        """Run scheduler"""
        print("="*60)
        print("[News Assistant] Scheduler started")
        print(f"   Morning: {PUSH_CONFIG['morning_time']}")
        print(f"   Evening: {PUSH_CONFIG['evening_time']}")
        print("="*60)
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.check_and_push()
                time.sleep(300)  # Check every 5 minutes
        except KeyboardInterrupt:
            print("\n\nService stopped")


def main():
    """Main entry"""
    import argparse
    
    parser = argparse.ArgumentParser(description='AI News Assistant')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--evening', action='store_true', help='Generate evening edition')
    parser.add_argument('--force', action='store_true', help='Force generation')
    parser.add_argument('--fast', action='store_true', help='Skip full-content extraction (faster)')
    
    args = parser.parse_args()
    
    assistant = NewsAssistant(fast_mode=args.fast)
    
    if args.once:
        assistant.run_once(force=args.force, is_morning=not args.evening)
    else:
        assistant.run_scheduler()


if __name__ == '__main__':
    main()
