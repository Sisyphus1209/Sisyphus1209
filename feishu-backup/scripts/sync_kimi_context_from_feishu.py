#!/usr/bin/env python3
"""
一键从飞书同步 Kimi 上下文资产。
前提：新环境已安装并认证 lark-cli（`lark-cli doctor` 通过）。

用法:
    python sync_kimi_context_from_feishu.py
    python sync_kimi_context_from_feishu.py --overwrite
"""

import argparse
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

LARK_CLI = "lark-cli"
BACKUP_NAME_PATTERN = "kimi-context-backup"
ZIP_NAME = "kimi-context-backup-latest.zip"

REQUIRED_FILES = [
    "AGENTS.md",
    "MEMORY.md",
    ".learnings/LEARNINGS.md",
    ".learnings/ERRORS.md",
]


def run(cmd, capture=True):
    """运行命令并返回 stdout 字符串。"""
    kwargs = {"shell": os.name == "nt"}
    if capture:
        kwargs["capture_output"] = True
        kwargs["text"] = True
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"Command failed: {cmd}", file=sys.stderr)
        if capture and result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip() if capture else ""


def find_latest_backup():
    """在飞书云盘中查找最新的上下文备份文件。"""
    jq_expr = (
        '.data.files '
        '| map(select(.name | contains("%s"))) '
        '| max_by(.modified_time) '
        '| {name: .name, token: .token, modified_time: .modified_time}'
    ) % BACKUP_NAME_PATTERN

    cmd = [LARK_CLI, "drive", "files", "list", "--format", "json", "-q", jq_expr]
    output = run(cmd)
    data = json.loads(output)

    if not data.get("name"):
        print("No backup file found in Feishu Drive matching '%s'" % BACKUP_NAME_PATTERN)
        sys.exit(1)

    return data["name"], data["token"], data["modified_time"]


def download_backup(file_token, output_path):
    """通过 file_token 下载备份文件。"""
    cmd = [
        LARK_CLI, "drive", "+download",
        "--file-token", file_token,
        "--output", str(output_path),
        "--overwrite",
    ]
    run(cmd, capture=False)


def extract_backup(zip_path, dest_dir):
    """解压备份到目标目录。"""
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest_dir)


def verify_files():
    """检查关键文件是否都已就位。"""
    missing = []
    for f in REQUIRED_FILES:
        if not Path(f).exists():
            missing.append(f)
    return missing


def main():
    parser = argparse.ArgumentParser(description="Sync Kimi context assets from Feishu Drive")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files without asking")
    parser.add_argument("--dest", default=".", help="Destination directory (default: current directory)")
    args = parser.parse_args()

    dest = Path(args.dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    os.chdir(dest)

    # 检查已有文件
    existing = [f for f in REQUIRED_FILES if Path(f).exists()]
    if existing and not args.overwrite:
        print("The following files already exist in the destination:")
        for f in existing:
            print(f"  - {f}")
        ans = input("Overwrite? [y/N]: ").strip().lower()
        if ans not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    print("Finding latest backup in Feishu Drive...")
    name, token, mtime = find_latest_backup()
    print(f"Found: {name} (modified_time={mtime})")

    zip_path = dest / ZIP_NAME
    print(f"Downloading to {zip_path}...")
    # lark-cli +download requires relative path within current directory
    download_backup(token, ZIP_NAME)

    print("Extracting...")
    extract_backup(zip_path, dest)

    print("Verifying...")
    missing = verify_files()
    if missing:
        print("Warning: some expected files are missing:")
        for f in missing:
            print(f"  - {f}")
    else:
        print("All key files are in place.")

    # 清理 zip（可选）
    zip_path.unlink(missing_ok=True)
    print("Done. You can now start Kimi Code CLI in this directory.")


if __name__ == "__main__":
    main()
