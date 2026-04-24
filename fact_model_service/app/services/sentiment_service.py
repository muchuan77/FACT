from __future__ import annotations

from app.schemas.prediction import SentimentResponse
from app.utils.text_utils import DEFAULT_KEYWORDS, score_probability


SENTIMENT_MODEL_NAME = "mock-sentiment-model"


def predict_sentiment(text: str) -> SentimentResponse:
    """
    Mock sentiment classifier.

    Rules:
    - if text contains negative trigger words like “严重/恐慌/危险/事故”, probability increases.
    """
    negative_prob = score_probability(text, DEFAULT_KEYWORDS.negative_triggers, base=0.18, step=0.20)

    # Minimal tri-class mapping for now:
    # - high negative_prob => negative
    # - low negative_prob  => neutral (we keep it simple for MVP)
    label = "negative" if negative_prob >= 0.52 else "neutral"
    return SentimentResponse(
        text=text,
        sentiment_label=label,
        sentiment_probability=negative_prob,
        model_name=SENTIMENT_MODEL_NAME,
    )

