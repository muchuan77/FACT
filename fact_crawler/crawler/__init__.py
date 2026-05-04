from __future__ import annotations

from .models import OpinionItem

__all__ = ["OpinionItem", "run_task_once"]


def __getattr__(name: str):
    if name == "run_task_once":
        from .runner import run_task_once as _run_task_once

        return _run_task_once
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
