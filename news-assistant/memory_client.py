#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
News Assistant Memory Bridge
Integrates agent-memory for persistent preferences and history.
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add agent-memory src path (note: folder name has hyphen, can't import as package)
AGENT_MEMORY_SRC = Path(__file__).parent.parent / "skills" / "agent-memory" / "src"
if str(AGENT_MEMORY_SRC) not in sys.path:
    sys.path.insert(0, str(AGENT_MEMORY_SRC))

try:
    from memory import AgentMemory
    MEMORY_AVAILABLE = True
except Exception as e:
    MEMORY_AVAILABLE = False
    print(f"[Memory] agent-memory not available: {e}")


class NewsMemory:
    """Persistent memory wrapper for news assistant."""
    
    def __init__(self):
        self.mem = AgentMemory() if MEMORY_AVAILABLE else None
    
    def is_ready(self) -> bool:
        return self.mem is not None
    
    def load_preferences(self) -> dict:
        """Load user preferences from memory."""
        prefs = {
            "favorite_categories": [],
            "ignore_sources": [],
            "highlight_keywords": [],
        }
        if not self.mem:
            return prefs
        
        # Recall facts tagged with preference
        facts = self.mem.recall("news preference", tags=["preference"], limit=10)
        for f in facts:
            content = f.content.lower()
            if "category" in content or "领域" in content:
                prefs["favorite_categories"].append(f.content)
            if "ignore" in content or "忽略" in content:
                prefs["ignore_sources"].append(f.content)
            if "highlight" in content or "关注" in content:
                prefs["highlight_keywords"].append(f.content)
        
        return prefs
    
    def save_run(self, report_path: str, categories: list):
        """Remember that a report was generated."""
        if not self.mem:
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.mem.remember(
            f"News report generated at {now}: {report_path} | Categories: {', '.join(categories)}",
            tags=["news_assistant", "report"],
            source="observation"
        )
    
    def learn_from_feedback(self, action: str, outcome: str, insight: str):
        """Record a lesson from user feedback."""
        if not self.mem:
            return
        self.mem.learn(
            action=action,
            context="news_assistant",
            outcome=outcome,
            insight=insight
        )
    
    def recall_recent_reports(self, limit: int = 5) -> list:
        """Recall recent report records."""
        if not self.mem:
            return []
        facts = self.mem.recall("news report generated", tags=["news_assistant"], limit=limit)
        return [f.content for f in facts]
    
    def track_tool(self, name: str, tool_type: str, url: str):
        """Track an interesting tool/Skill/MCP for future reference."""
        if not self.mem:
            return
        self.mem.track_entity(
            name=name,
            entity_type=tool_type,
            attributes={"url": url, "first_seen": datetime.now().isoformat()}
        )
    
    def list_tracked_tools(self) -> list:
        """List tools that have been tracked."""
        if not self.mem:
            return []
        entities = self.mem.list_entities(entity_type="tool")
        return [(e.name, e.attributes.get("url", "")) for e in entities]


if __name__ == "__main__":
    nm = NewsMemory()
    print("Memory ready:", nm.is_ready())
    if nm.is_ready():
        prefs = nm.load_preferences()
        print("Preferences:", prefs)
        nm.save_run("news_reports/test.md", ["tech_ai", "devtools"])
        print("Recent reports:", nm.recall_recent_reports())
