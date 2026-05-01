from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional

import requests

from .models import OpinionItem


class BackendClient:
    def __init__(self, base_url: str, *, timeout: float = 10.0, dry_run: bool = False):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.dry_run = dry_run

    def create_opinion(self, item: OpinionItem) -> Dict[str, Any]:
        if self.dry_run:
            return {"dry_run": True, "id": None}
        payload = {
            "title": item.title,
            "content": item.content,
            "source": item.source,
            "source_url": item.source_url,
            "publish_time": item.publish_time.isoformat() if item.publish_time else None,
            "category": item.category,
            "raw_label": item.raw_label,
            "keywords": item.keywords,
        }
        resp = requests.post(f"{self.base_url}/api/opinions/", json=payload, timeout=self.timeout)
        if resp.status_code >= 400:
            raise RuntimeError(f"create_opinion failed: http {resp.status_code}: {resp.text}")
        return resp.json()

    def analyze_opinion(self, opinion_id: int) -> Dict[str, Any]:
        if self.dry_run:
            return {"dry_run": True}
        resp = requests.post(f"{self.base_url}/api/opinions/{opinion_id}/analyze/", json={}, timeout=self.timeout)
        if resp.status_code >= 400:
            raise RuntimeError(f"analyze_opinion failed: http {resp.status_code}: {resp.text}")
        return resp.json()

