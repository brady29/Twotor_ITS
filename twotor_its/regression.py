"""Linear regression inference for performance forecasting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class RegressionWeights:
    intercept: float
    coefficients: Dict[str, float]


class LinearRegressionModel:
    

    def __init__(self, weights: RegressionWeights):
        self.weights = weights

    def predict(self, features: Dict[str, float]) -> float:
        value = self.weights.intercept
        for name, coef in self.weights.coefficients.items():
            value += coef * features.get(name, 0.0)
        return value

    def predict_clipped(self, features: Dict[str, float], low: float = 0, high: float = 100) -> float:
        return max(low, min(high, self.predict(features)))

#fixed weights for regression model
def default_regression_model() -> LinearRegressionModel:
    weights = RegressionWeights(
        intercept=5.0,
        coefficients={
            "avg_mastery": 30.0,
            "recent_attempt_score": 0.6,
            "attempts_last_week": 0.5,
            "question_difficulty": -5.0,
        },
    )
    return LinearRegressionModel(weights=weights)
