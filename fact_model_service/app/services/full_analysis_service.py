from __future__ import annotations

from app.schemas.prediction import FullAnalysisResponse
from app.services.rumor_service import predict_rumor
from app.services.sentiment_service import predict_sentiment
from app.utils.text_utils import extract_keywords, suggested_risk_level


FULL_MODEL_NAME = "mock-full-analysis-model"


def full_analyze_text(text: str) -> FullAnalysisResponse:
    rumor = predict_rumor(text)
    sentiment = predict_sentiment(text)
    keywords = extract_keywords(text)
    risk = suggested_risk_level(rumor.rumor_probability, sentiment.sentiment_probability)

    return FullAnalysisResponse(
        text=text,
        rumor_label=rumor.rumor_label,
        rumor_probability=rumor.rumor_probability,
        sentiment_label=sentiment.sentiment_label,
        sentiment_probability=sentiment.sentiment_probability,
        keywords=keywords,
        suggested_risk_level=risk,
        model_name=FULL_MODEL_NAME,
    )

