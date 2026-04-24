from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


def _contains_any(text: str, keywords: Iterable[str]) -> bool:
    return any(k in text for k in keywords)


def _count_hits(text: str, keywords: Iterable[str]) -> int:
    return sum(1 for k in keywords if k in text)


def clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def score_probability(text: str, trigger_words: List[str], base: float = 0.2, step: float = 0.18) -> float:
    """
    Deterministic mock scoring:
    - start from base
    - add step per matched trigger word
    - clamp to [0, 0.95] to keep "probability-like" behavior
    """
    hits = _count_hits(text, trigger_words)
    # 命中越多，增长越快（但仍保持确定性与上限）
    bonus = 0.0
    if hits >= 2:
        bonus += 0.06
    if hits >= 4:
        bonus += 0.06
    prob = base + hits * step + bonus
    return min(0.95, clamp01(prob))


@dataclass(frozen=True)
class KeywordConfig:
    rumor_triggers: List[str]
    negative_triggers: List[str]
    keyword_bank: List[str]


DEFAULT_KEYWORDS = KeywordConfig(
    rumor_triggers=[
        "网传",
        "爆料",
        "谣言",
        "不实",
        "辟谣",
        "造谣",
        "传言",
        "偷拍视频",
        "震惊",
        "恐慌",
        "严重",
    ],
    negative_triggers=[
        "严重",
        "恐慌",
        "危险",
        "事故",
        "火灾",
        "爆炸",
        "地震",
        "疫情",
        "中毒",
        "暴力",
        "伤亡",
        "坠楼",
        "诈骗",
        "拐卖",
        "校园",
        "学生",
    ],
    keyword_bank=[
        # 通用
        "网传",
        "爆料",
        "关注",
        "谣言",
        "不实",
        "辟谣",
        "造谣",
        "传言",
        "恐慌",
        "严重",
        "危险",
        # 公共安全
        "事故",
        "火灾",
        "爆炸",
        "地震",
        "暴雨",
        "洪水",
        "塌方",
        "伤亡",
        "救援",
        # 校园舆情
        "学校",
        "学生",
        "校园",
        "老师",
        "欺凌",
        "猥亵",
        # 社会风险
        "诈骗",
        "拐卖",
        "暴力",
        "斗殴",
        "抢劫",
        "中毒",
        # 医疗健康
        "疫情",
        "感染",
        "病例",
        "食品安全",
        "疫苗",
        # 经济金融
        "金融",
        "爆雷",
        "跑路",
        "诈骗",
    ],
)


def extract_keywords(text: str, bank: List[str] | None = None, max_keywords: int = 5) -> List[str]:
    bank = bank or DEFAULT_KEYWORDS.keyword_bank
    hits = [k for k in bank if k in text]
    # de-dup, keep order
    uniq: List[str] = []
    for k in hits:
        if k not in uniq:
            uniq.append(k)
        if len(uniq) >= max_keywords:
            break
    return uniq


def suggested_risk_level(rumor_prob: float, sentiment_prob: float, high_threshold: float = 0.75) -> str:
    rumor_high = rumor_prob >= high_threshold
    sentiment_high = sentiment_prob >= high_threshold
    if rumor_high and sentiment_high:
        return "high"
    if rumor_high or sentiment_high:
        return "medium"
    return "low"

