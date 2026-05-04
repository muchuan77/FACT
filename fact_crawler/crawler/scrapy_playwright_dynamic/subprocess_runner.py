"""
独立进程入口：避免在 Django 同进程内启动 Twisted reactor / Playwright。

stdin: UTF-8 JSON 配置（父进程 json.dumps(..., ensure_ascii=False).encode("utf-8")）
stdout: 仅一行 JSON 数组（ensure_ascii=True）
stderr: 诊断日志
"""

from __future__ import annotations

import json
import sys


def main() -> None:
    raw = sys.stdin.buffer.read()
    cfg = json.loads(raw.decode("utf-8"))
    from .run_spider import run_collect_raw

    rows = run_collect_raw(cfg)
    sys.stdout.write(json.dumps(rows, ensure_ascii=True))
    sys.stdout.flush()


if __name__ == "__main__":
    main()
