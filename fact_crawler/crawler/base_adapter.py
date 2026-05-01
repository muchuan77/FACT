from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterable, Sequence

from .models import OpinionItem


@dataclass
class AdapterContext:
    source_name: str
    base_url: str
    task_type: str  # monitor / search
    keywords: list[str]
    exclude_keywords: list[str]
    risk_words: list[str]
    category: str
    max_items: int


class BaseAdapter(ABC):
    adapter_name: str

    @abstractmethod
    def fetch(self, ctx: AdapterContext) -> list[OpinionItem]:
        raise NotImplementedError

