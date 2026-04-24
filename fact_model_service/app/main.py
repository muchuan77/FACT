from fastapi import FastAPI

from app.schemas.prediction import (
    FullAnalysisResponse,
    SentimentResponse,
    TextRequest,
    RumorResponse,
)
from app.services.full_analysis_service import full_analyze_text
from app.services.rumor_service import predict_rumor
from app.services.sentiment_service import predict_sentiment


app = FastAPI(title="FACT model service", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "FACT model service"}


@app.post("/predict/rumor", response_model=RumorResponse)
def predict_rumor_api(payload: TextRequest):
    return predict_rumor(payload.text)


@app.post("/predict/sentiment", response_model=SentimentResponse)
def predict_sentiment_api(payload: TextRequest):
    return predict_sentiment(payload.text)


@app.post("/predict/full", response_model=FullAnalysisResponse)
def predict_full_api(payload: TextRequest):
    return full_analyze_text(payload.text)

