#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek Translator for News Assistant
Uses DeepSeek API (OpenAI-compatible) for high-quality Chinese translation.
Falls back to MyMemory free API if no key is provided.
"""

import os
import time
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed


def _get_config():
    """Load translation config from config.py"""
    try:
        from config import TRANSLATION_API_CONFIG
        return TRANSLATION_API_CONFIG
    except Exception:
        return {
            "provider": "memory",
            "api_key": "",
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat",
            "max_tokens": 2048,
        }


def _call_deepseek_single(text: str, api_key: str, base_url: str, model: str, max_tokens: int) -> str:
    """Call DeepSeek API for single text translation."""
    try:
        import requests
        url = f"{base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a professional translator. "
                        "Translate the following English text into natural, fluent Chinese. "
                        "Keep technical terms accurate. Do not add explanations, only return the translation."
                    )
                },
                {"role": "user", "content": text}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        data = resp.json()
        if resp.status_code == 200 and "choices" in data:
            return data["choices"][0]["message"]["content"].strip()
        else:
            # API error, fallback
            return text
    except Exception:
        return text


def translate_with_deepseek(texts: List[str]) -> List[str]:
    """
    Translate a list of texts using DeepSeek API with 5-worker threadpool.
    Falls back to MyMemory if no API key is configured.
    """
    cfg = _get_config()
    api_key = cfg.get("api_key", "") or os.getenv("DEEPSEEK_API_KEY", "")
    
    if not api_key or api_key.strip() == "":
        # Fallback to free MyMemory translator
        return _translate_with_mymemory(texts)
    
    base_url = cfg.get("base_url", "https://api.deepseek.com/v1")
    model = cfg.get("model", "deepseek-chat")
    max_tokens = cfg.get("max_tokens", 2048)
    
    results = [""] * len(texts)
    
    def _worker(idx_text):
        idx, text = idx_text
        if not text or not text.strip():
            return idx, text
        # Add small delay to avoid rate limit
        if idx > 0 and idx % 5 == 0:
            time.sleep(0.5)
        translated = _call_deepseek_single(text, api_key, base_url, model, max_tokens)
        return idx, translated
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(_worker, (i, t)) for i, t in enumerate(texts)]
        for future in as_completed(futures):
            idx, translated = future.result()
            results[idx] = translated
    
    return results


def _translate_with_mymemory(texts: List[str]) -> List[str]:
    """Fallback free translator using deep_translator MyMemory."""
    try:
        from deep_translator import MyMemoryTranslator
        t = MyMemoryTranslator(source='en-US', target='zh-CN')
        # MyMemory free tier has limits, process in small batches with delay
        results = []
        for i, text in enumerate(texts):
            if not text or not text.strip():
                results.append(text)
                continue
            try:
                results.append(t.translate(text))
            except Exception:
                results.append(text)
            if (i + 1) % 3 == 0:
                time.sleep(0.3)
        return results
    except Exception:
        return texts


if __name__ == "__main__":
    samples = [
        "Tesla FSD v12 rolling out to more customers.",
        "SpaceX Starship Flight 4 scheduled this month.",
    ]
    out = translate_with_deepseek(samples)
    for s, o in zip(samples, out):
        print(f"EN: {s}")
        print(f"ZH: {o}")
        print()
