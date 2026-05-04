"""
独立进程入口：避免在 Django 同进程内启动 Twisted reactor。

stdin: JSON 配置（建议 ASCII 转义，父进程 ensure_ascii=True）
stdout: 仅一行 JSON 数组（ensure_ascii=True，避免 Windows 控制台编码污染）
stderr: 可写调试信息，勿写 stdout
"""

from __future__ import annotations

import json
import sys


def main() -> None:
    cfg = json.load(sys.stdin)
    from .run_spider import run_collect_raw

    rows = run_collect_raw(cfg)
    # 仅 ASCII：父进程用 UTF-8 解码 stdout 后 json.loads 仍得到正确 Unicode
    sys.stdout.write(json.dumps(rows, ensure_ascii=True))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
