#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于风格模板创建网易云歌单
用法:
    python create_playlist_by_style.py --styles melodic_rap_cn melodic_rap_en western_classical --name "AI推荐 | 旋律说唱+古典 vibe"
"""
import argparse
import json
import time
from pathlib import Path

from pyncm import LoadSessionFromString, SetCurrentSession
from pyncm.apis.playlist import SetCreatePlaylist, SetManipulatePlaylistTracks, GetPlaylistAllTracks

from fetch_recommendations import fetch_pool_by_template


def load_liked_ids():
    tracks = json.loads(Path('netease_tracks.json').read_text(encoding='utf-8'))
    return set(t['id'] for t in tracks)


def load_template(name):
    tpl_path = Path(__file__).parent.parent / 'templates' / f'{name}.json'
    return json.loads(tpl_path.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser(description='Create NetEase playlist from style templates')
    parser.add_argument('--styles', nargs='+', required=True, help='Template names (e.g. melodic_rap_cn melodic_rap_en western_classical)')
    parser.add_argument('--name', required=True, help='Playlist name')
    parser.add_argument('--privacy', choices=['public', 'private'], default='public', help='Playlist privacy')
    args = parser.parse_args()

    # auth
    cred = Path.home() / '.pyncm_credential.json'
    text = cred.read_text(encoding='utf-8')
    session = LoadSessionFromString(text)
    SetCurrentSession(session)

    liked_ids = load_liked_ids()
    print(f'已红心歌曲数: {len(liked_ids)}')

    composition = {}
    playlist_tracks = []

    for style_name in args.styles:
        tpl = load_template(style_name)
        print(f"\n正在抓取风格: {tpl['name']} ...")
        pool = fetch_pool_by_template(tpl, liked_ids)
        count = tpl.get('default_count', 10)
        selected = pool[:count]
        composition[style_name] = {
            'label': tpl['name'],
            'count': len(selected),
            'candidates_after_filter': len(pool)
        }
        playlist_tracks.extend(selected)
        print(f"  候选池: {len(pool)}, 入选: {len(selected)}")

    print(f'\n歌单总计: {len(playlist_tracks)} 首')
    for k, v in composition.items():
        print(f"  {v['label']}: {v['count']} 首")

    if len(playlist_tracks) == 0:
        print('没有可用歌曲，终止创建')
        return

    # create playlist
    is_public = args.privacy == 'public'
    print(f"\n创建歌单: {args.name} (public={is_public})")
    create_result = SetCreatePlaylist(args.name, privacy=not is_public)
    new_pid = create_result.get('id')
    print(f'歌单ID: {new_pid}')

    if not new_pid:
        print('创建失败')
        return

    # add tracks (correct param order: trackIds, playlistId)
    track_ids = [str(t['id']) for t in playlist_tracks]
    for i in range(0, len(track_ids), 100):
        batch = track_ids[i:i+100]
        result = SetManipulatePlaylistTracks(batch, new_pid, op='add')
        status = result.get('code', result)
        print(f'  批次 {i//100 + 1} ({len(batch)}首): code={status}')

    # verify
    print('\n验证歌单内容...')
    time.sleep(2)
    current = GetPlaylistAllTracks(new_pid)
    actual_count = len(current.get('songs', []))
    print(f'实际歌曲数: {actual_count} / {len(playlist_tracks)}')

    if actual_count == 0:
        print('歌单为空，正在重试...')
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i:i+100]
            result = SetManipulatePlaylistTracks(batch, new_pid, op='add')
            code = result.get('code', result)
            print(f'  重试批次 {i//100 + 1}: code={code}')
        time.sleep(2)
        current2 = GetPlaylistAllTracks(new_pid)
        actual_count = len(current2.get('songs', []))
        print(f'重试后: {actual_count} 首')

    # save report
    report = {
        'playlist_name': args.name,
        'playlist_id': new_pid,
        'track_count': len(playlist_tracks),
        'actual_count': actual_count,
        'is_public': is_public,
        'composition': composition,
    }
    report_path = Path('netease_playlist_report_latest.json')
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    if actual_count > 0:
        print(f'\n[OK] 歌单创建成功: {new_pid}')
    else:
        print('\n[FAIL] 歌单为空，请检查 API。')


if __name__ == '__main__':
    main()
