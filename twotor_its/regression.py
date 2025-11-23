"""Linear regression inference for performance forecasting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class RegressionWeights:
    intercept: float
    coefficients: Dict[str, float]


class LinearRegressionModel:
    """Tiny linear model with fixed, pre-trained weights."""

    def __init__(self, weights: RegressionWeights):
        self.weights = weights

    def predict(self, features: Dict[str, float]) -> float:
        value = self.weights.intercept
        for name, coef in self.weights.coefficients.items():
            value += coef * features.get(name, 0.0)
        return value

    def predict_clipped(self, features: Dict[str, float], low: float = 0, high: float = 100) -> float:
        return max(low, min(high, self.predict(features)))


def default_regression_model() -> LinearRegressionModel:
    weights = RegressionWeights(
        intercept=22.0,
        coefficients={
            "avg_mastery": 55.0,
            "recent_attempt_score": 0.35,
            "time_spent_minutes": 0.8,
            "attempts_last_week": -1.5,
            "question_difficulty": -4.0,
        },
    )
    return LinearRegressionModel(weights=weights)
