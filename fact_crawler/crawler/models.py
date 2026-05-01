from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class OpinionItem:
    title: str
    content: str
    source: str
    source_url: str
    publish_time: Optional[datetime]
    category: str
    raw_label: str = "unknown"
    keywords: list[str] = None  # type: ignore[assignment]
    task_id: Optional[int] = None
    run_id: Optional[int] = None

    def __post_init__(self) -> None:
        if self.keywords is None:
            self.keywords = []

