---
name: feishu-backup
description: |
  当用户需要备份 Kimi 上下文资产（AGENTS.md / MEMORY.md / .learnings / Obsidian Vault）到飞书云盘，
  或在新机器上一键恢复这些资产时，使用此 skill。
  触发词：「备份到飞书」「恢复上下文」「kimi 同步」「换电脑恢复」「飞书云盘备份」「
  sync_kimi_context」「上下文灾难恢复」
---

# Feishu Backup · Kimi 上下文同步

## 使用说明

本 skill 提供两条链路：
1. **备份链路**：把 `AGENTS.md`、`MEMORY.md`、`.learnings/`、`Obsidian Vault/` 打包成 zip，上传到飞书云盘。
2. **恢复链路**：在新机器上运行脚本，自动从飞书云盘拉取最新备份并解压恢复。

## 前置条件

- 已安装并认证 `lark-cli`（运行 `lark-cli doctor` 确认通过）
- Windows 环境（脚本已针对 PowerShell 执行策略和路径空格做适配）

## 备份流程

### 手动备份（推荐每次重大更新后执行）

```powershell
# 1. 打包
Compress-Archive -Path AGENTS.md,MEMORY.md,.learnings,"Documents\Obsidian Vault" -DestinationPath kimi-context-backup-$(Get-Date -Format yyyyMMdd).zip

# 2. 上传到飞书云盘
cmd.exe /c "lark-cli drive +upload --file kimi-context-backup-20260408.zip --folder-token <YOUR_FOLDER_TOKEN>"
```

> 为什么用 `cmd.exe /c`？因为 `lark-cli` 在 PowerShell 下可能因执行策略报错，用 cmd  wrapper 最稳。

## 恢复流程

### 一键恢复（新机器）

脚本已内置在 `scripts/sync_kimi_context_from_feishu.py`。

```bash
python sync_kimi_context_from_feishu.py --overwrite
```

### 脚本行为
1. 调用 `lark-cli drive files list` 查找文件名含 `kimi-context-backup` 的最新 zip
2. 下载到当前目录
3. 解压覆盖
4. 检查 `AGENTS.md`、`MEMORY.md`、`.learnings/LEARNINGS.md`、`.learnings/ERRORS.md` 是否存在
5. 清理临时 zip

## 文件清单

| 文件 | 用途 |
|------|------|
| `scripts/sync_kimi_context_from_feishu.py` | 自动恢复脚本 |
| `README_Backup.md` | 备份操作备忘 |

## 核心设计决策

- **zip 而非 git**：用户不想管理 diff，只想"整个目录换电脑能活"
- **时间戳命名**：避免覆盖旧版本，保留历史备份
- `--overwrite**：明确告知用户会覆盖本地文件，防止误操作
- **验证步骤**：恢复后必须检查关键文件，避免空包或损坏包

## 诚实边界

- 此 skill 依赖 `lark-cli` 的认证状态；如果 token 过期，需要先重新登录
- 大体积 Obsidian Vault 可能导致 zip 超过飞书单文件上传限制（需确认企业版限制）
- 不包含自动定时备份，需要用户手动触发或自行配置 Windows 任务计划程序
