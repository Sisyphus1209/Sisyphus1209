#!/usr/bin/env python3
"""Today's News Briefing"""

from datetime import datetime
from pathlib import Path
import subprocess
import sys

def main():
    now = datetime.now()
    
    content = f"""# News Brief - {now.strftime('%Y-%m-%d %H:%M')}

## Elon Musk Updates
- Tesla FSD v12 rolling out to more customers
- SpaceX Starship Flight 4 scheduled this month
- xAI Grok 2 training progressing well

## Tech/AI
- OpenAI GPT-5 development shows significant progress
- NVIDIA Q4 earnings: data center revenue up 279%
- Google Gemini 1.5 Pro: 2M token context window

## Finance
- Federal Reserve signals potential rate cuts
- Bitcoin ETFs seeing continued inflows

## Robotics
- Tesla Optimus shows improved walking and manipulation
- Humanoid robot competition heating up

*Generated: {now.strftime('%Y-%m-%d %H:%M')}*
"""
    
    # Save
    out_dir = Path('news_reports')
    out_dir.mkdir(parents=True, exist_ok=True)
    filepath = out_dir / f"news_{now.strftime('%Y%m%d_%H%M')}.md"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Report saved: {filepath}")
    
    # Open with notepad (non-blocking)
    try:
        subprocess.Popen(['notepad', str(filepath)], shell=True)
        print("Opening with Notepad...")
    except:
        print(f"Please open manually: {filepath}")
    
    return filepath

if __name__ == '__main__':
    main()
