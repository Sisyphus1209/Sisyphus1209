#!/usr/bin/env python3
"""
Generate demo report without network
"""

from datetime import datetime, timedelta
import os
from pathlib import Path

def generate_demo_report():
    """Generate a demo news report"""
    now = datetime.now()
    
    report = f"""# News Brief - Morning Edition ({now.strftime('%Y-%m-%d %H:%M')})

---

## Elon Musk Updates

**{now.strftime('%Y-%m-%d %H:%M')}**
> Tesla FSD v12 rolling out to more customers. End-to-end neural network improvements are remarkable.
  Likes: 45,200 | Retweets: 8,900
  [View on X](https://twitter.com/elonmusk)

**{(now - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M')}**
> SpaceX Starship Flight 4 scheduled this month. Major heat shield and flap design improvements.
  Likes: 67,800 | Retweets: 12,300
  [View on X](https://twitter.com/elonmusk)

---

## Tech/AI

### 1. OpenAI Announces GPT-5 Development Progress
*TechCrunch* | 08:30

**Summary**: OpenAI has revealed significant progress on GPT-5, with improved reasoning capabilities and multimodal understanding...

**Key Terms**:
- **GPT**: Generative Pre-trained Transformer, a type of large language model
- **Multimodal**: AI that can process text, images, audio together
- **Reasoning**: AI's ability to think through problems step by step

[Read more](https://techcrunch.com)

### 2. NVIDIA Revenue Exceeds Expectations
*Reuters* | 07:15

**Summary**: NVIDIA reported Q4 earnings with data center revenue up 279% year-over-year, driven by AI chip demand...

**Key Terms**:
- **Data Center**: Facilities housing computing infrastructure
- **GPU**: Graphics Processing Unit, essential for AI training
- **Revenue YoY**: Year-over-year comparison

**Background**: NVIDIA has become the dominant supplier of AI training chips, with their A100 and H100 GPUs being used by virtually every major AI lab.

[Read more](https://reuters.com)

---

## Finance

### 1. Federal Reserve Signals Rate Cut Timeline
*BBC Business* | 09:00

**Summary**: Fed Chair indicated potential rate cuts in coming months if inflation continues cooling...

**Key Terms**:
- **Federal Reserve**: US central bank controlling monetary policy
- **Rate Cut**: Lowering interest rates to stimulate economy
- **Inflation**: Rate of price increases in the economy

**Background**: The Fed raised rates aggressively in 2022-2023 to combat inflation. Markets are watching for the pivot to rate cuts.

[Read more](https://bbc.com)

---

## Robotics

### 1. Tesla Optimus Robot Demonstrates New Capabilities
*The Robot Report* | 10:30

**Summary**: Tesla's humanoid robot Optimus shows improved walking and object manipulation in latest demo...

**Key Terms**:
- **Humanoid Robot**: Robot designed to look and move like humans
- **Optimus**: Tesla's humanoid robot project
- **Actuator**: Device that converts energy to motion

**Background**: Tesla aims to produce millions of Optimus robots for factory work and eventually consumer use. Competitors include Boston Dynamics and Figure AI.

[Read more](https://therobotreport.com)

---

*This is a demo report. Real-time news will be fetched when network is available.*
*Generated: {now.strftime('%Y-%m-%d %H:%M')}*
"""
    
    # Save report
    output_dir = Path('news_reports')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = now.strftime("%Y%m%d_%H%M")
    filepath = output_dir / f"news_morning_{timestamp}.md"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Demo report saved: {filepath}")
    
    # Open report
    try:
        os.startfile(filepath)
    except:
        pass
    
    return filepath


if __name__ == '__main__':
    generate_demo_report()
