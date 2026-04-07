---
name: netease-playlist
description: |
  当用户要求创建网易云音乐歌单、推荐新歌、生成基于特定风格的播放列表时，使用此 skill。
  触发词包括："给我建个歌单"、"推荐点歌"、"旋律说唱"、"英文说唱"、"古典"、"网易云歌单"、"没听过的音乐" 等。
  必须优先读取用户红心歌单（netease_tracks.json）进行过滤，确保推荐的是新鲜歌曲。
---



# NetEase Playlist Skill
## 用户核心偏好（不可违背）
1. **拒绝中国传统音乐**：歌单里绝对不要出现古筝、古琴、二胡、琵琶、笛子、唢呐、广陵散、国风民乐等。
2. **"古典" = 西方古典**：莫扎特、贝多芬、肖邦、巴赫、维瓦尔第、柴可夫斯基、舒伯特、德彪西、海顿、舒曼等。
4. **公开歌单**：`SetCreatePlaylist(..., privacy=False)`，不能上锁。
5. **验证非空**：创建后必须调用 `GetPlaylistAllTracks` 回查歌曲数量，避免空歌单。
## 可用的风格模板
| 模板文件名 | 风格 | 默认数量 |
|-----------|------|---------|
| `melodic_rap_cn.json` | 中文旋律说唱 | 20 |
| `melodic_rap_en.json` | 英文旋律说唱 | 20 |
| `western_classical.json` | 西方古典 | 6 |
| `indie_rock.json` | 独立摇滚 | 15 |
## 执行流程
### 1. 解析用户请求
- 提取歌单名称（如用户未指定，自动生成：`AI推荐 | {风格} vibe`）
- 提取风格组合（如"旋律说唱+古典"、"中英文对半分"）
- 确定是否公开（默认公开）
### 2. 加载数据
- 读取 `netease_tracks.json` 获取已红心歌曲 ID
- 读取对应的模板 JSON 文件
### 3. 抓取与过滤
- 对每个模板中的关键词调用 `GetSearchResult(keyword, stype=1, limit=...)`
- 去重、过滤已红心、过滤 `exclude_keywords`
- 按模板 `default_count` 截取
### 4. 创建与验证
- 创建公开歌单
- 分批添加歌曲（每批不超过 100 首）
- 2 秒后回查验证 `actual_count`
- 如果为空，立即重试一次
### 5. 输出结果
- 报告歌单 ID、实际歌曲数、各风格占比
- 将结果写入 `netease_playlist_report_latest.json`
## 脚本入口
```bash
python skills/netease-playlist/scripts/create_playlist_by_style.py \
  --styles melodic_rap_cn melodic_rap_en western_classical \
  --name "AI推荐 | 旋律说唱+古典 vibe" \
  --privacy public
```
## 常见组合速查
| 用户需求 | 命令示例 |
|---------|---------|
| 中英文旋律说唱对半 + 少量西方古典 | `--styles melodic_rap_cn melodic_rap_en western_classical` |
| 纯中文旋律说唱 | `--styles melodic_rap_cn --name "AI推荐 | 中文旋律说唱"` |
| 纯英文旋律说唱 | `--styles melodic_rap_en --name "AI推荐 | 英文旋律说唱"` |
| 独立摇滚 | `--styles indie_rock --name "AI推荐 | Indie Rock"` |
## 避坑 Checklist
- [ ] 认证文件 `~/.pyncm_credential.json` 存在且有效
- [ ] `netease_tracks.json` 已读取，红心 ID 已过滤
- [ ] `SetCreatePlaylist` 的 `privacy=False`（公开）
- [ ] `SetManipulatePlaylistTracks(batch, new_pid, op='add')` 参数顺序正确
- [ ] 创建后 `GetPlaylistAllTracks` 验证 `actual_count > 0`
- [ ] 结果里没有古筝/古琴/二胡/琵琶/广陵散等中国传统音乐
