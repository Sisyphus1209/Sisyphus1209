#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可复用的网易云推荐歌曲抓取模块
"""
import time
from pyncm.apis.cloudsearch import GetSearchResult


def search_tracks(keyword, limit=15):
    """搜索歌曲，返回候选列表"""
    try:
        result = GetSearchResult(keyword, stype=1, limit=limit)
        songs = result.get('result', {}).get('songs', [])
        tracks = []
        for s in songs:
            tracks.append({
                'id': s['id'],
                'name': s['name'],
                'artists': [a['name'] for a in s.get('artists', []) if a.get('name')],
            })
        return tracks
    except Exception as e:
        print(f'搜索失败 [{keyword}]: {e}')
        return []


def dedup_and_filter(tracks, exclude_ids, exclude_keywords=None):
    """去重、过滤已红心、过滤包含排除关键词的歌曲"""
    seen = set()
    out = []
    exclude_keywords = exclude_keywords or []
    for t in tracks:
        rid = t['id']
        if rid in seen or rid in exclude_ids:
            continue
        # 检查排除关键词
        combined = (t['name'] + ' ' + ' '.join(t['artists'])).lower()
        if any(kw.lower() in combined for kw in exclude_keywords):
            continue
        seen.add(rid)
        out.append(t)
    return out


def fetch_pool_by_template(template, liked_ids, sleep_sec=0.25):
    """根据模板配置抓取候选池"""
    pool = []
    limit = template.get('search_limit', 8)
    keywords = template.get('keywords', [])
    for kw in keywords:
        pool.extend(search_tracks(kw, limit=limit))
        time.sleep(sleep_sec)
    exclude_keywords = template.get('exclude_keywords', [])
    return dedup_and_filter(pool, liked_ids, exclude_keywords)
