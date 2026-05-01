from __future__ import annotations

import re


DEFAULT_RISK_WORDS = [
    "网传",
    "爆料",
    "事故",
    "风险",
    "通报",
    "诈骗",
    "火灾",
    "疫情",
    "食品安全",
    "学生",
    "学校",
    "举报",
    "投诉",
    "舆情",
    "谣言",
    "澄清",
]


def extract_keywords(title: str, content: str, *, risk_words: list[str] | None = None, limit: int = 8) -> list[str]:
    """
    轻量关键词提取：风险词优先 + 简单分词片段（2~6 汉字或英文词）。
    去重保序，最多 limit 个。
    """
    risk_words = risk_words or DEFAULT_RISK_WORDS
    text = f"{title} {content}".strip()

    out: list[str] = []
    for w in risk_words:
        if w and w in text and w not in out:
            out.append(w)
        if len(out) >= limit:
            return out[:limit]

    tokens = re.findall(r"[\u4e00-\u9fff]{2,6}|[A-Za-z]{3,16}", text)
    for t in tokens:
        t = t.strip()
        if not t or t in out:
            continue
        out.append(t)
        if len(out) >= limit:
            break
    return out[:limit]

