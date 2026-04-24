from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ModelServiceConfig:
    """
    预留模型服务调用配置（MVP：只定义结构，不强制要求服务在线）。
    """

    base_url: str = "http://127.0.0.1:8001"
    timeout_seconds: float = 5.0


def predict_full(text: str, config: Optional[ModelServiceConfig] = None) -> Dict[str, Any]:
    """
    预留：调用 FastAPI 模型服务的 /predict/full 接口。

    说明：
    - 当前阶段仅提供函数结构与返回约定，不强制依赖真实服务是否启动。
    - 后续接入时可在此处加入 requests 调用与异常处理、重试、降级等逻辑。
    """
    cfg = config or ModelServiceConfig()

    # 当前阶段默认不强制调用远端服务；保留结构与异常处理，便于后续直接接入。
    try:
        import requests  # 延迟导入，避免在未安装依赖时直接报错

        url = f"{cfg.base_url.rstrip('/')}/predict/full"
        resp = requests.post(url, json={"text": text}, timeout=cfg.timeout_seconds)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "text" in data:
            return data
    except Exception as exc:
        return {
            "text": text,
            "rumor_label": "unknown",
            "rumor_probability": 0.0,
            "sentiment_label": "unknown",
            "sentiment_probability": 0.0,
            "keywords": [],
            "suggested_risk_level": "low",
            "model_name": "placeholder-model-client",
            "note": "model service call not available in this stage",
            "error": str(exc),
        }

    return {
        "text": text,
        "rumor_label": "unknown",
        "rumor_probability": 0.0,
        "sentiment_label": "unknown",
        "sentiment_probability": 0.0,
        "keywords": [],
        "suggested_risk_level": "low",
        "model_name": "placeholder-model-client",
        "note": "model service call disabled / invalid response",
    }

