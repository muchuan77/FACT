from typing import List, Literal

from pydantic import BaseModel, Field


class TextRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Input text to analyze")


RumorLabel = Literal["rumor", "non_rumor"]
SentimentLabel = Literal["positive", "neutral", "negative"]
RiskLevel = Literal["low", "medium", "high"]


class RumorResponse(BaseModel):
    text: str
    rumor_label: RumorLabel
    rumor_probability: float = Field(..., ge=0.0, le=1.0)
    model_name: str


class SentimentResponse(BaseModel):
    text: str
    sentiment_label: SentimentLabel
    sentiment_probability: float = Field(..., ge=0.0, le=1.0)
    model_name: str


class FullAnalysisResponse(BaseModel):
    text: str
    rumor_label: RumorLabel
    rumor_probability: float = Field(..., ge=0.0, le=1.0)
    sentiment_label: SentimentLabel
    sentiment_probability: float = Field(..., ge=0.0, le=1.0)
    keywords: List[str]
    suggested_risk_level: RiskLevel
    model_name: str

