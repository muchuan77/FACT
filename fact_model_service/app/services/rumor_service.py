from __future__ import annotations

from app.schemas.prediction import RumorResponse
from app.utils.text_utils import DEFAULT_KEYWORDS, score_probability


RUMOR_MODEL_NAME = "mock-rumor-model"


def predict_rumor(text: str) -> RumorResponse:
    """
    Mock rumor classifier.

    Rules:
    - if text contains trigger words like “网传/谣言/不实/恐慌/严重”, probability increases.
    """
    rumor_prob = score_probability(text, DEFAULT_KEYWORDS.rumor_triggers, base=0.22, step=0.19)
    label = "rumor" if rumor_prob >= 0.6 else "non_rumor"
    return RumorResponse(
        text=text,
        rumor_label=label,
        rumor_probability=rumor_prob,
        model_name=RUMOR_MODEL_NAME,
    )

