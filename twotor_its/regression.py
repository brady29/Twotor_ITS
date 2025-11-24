"""Linear regression inference for performance forecasting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Iterable, Optional
from math import inf
from sklearn.linear_model import LinearRegression # type: ignore

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

#fixed weights for regression model if training fails or isnt possible
def default_regression_model() -> LinearRegressionModel:

    weights = RegressionWeights(
        intercept=157.3019150459153,
        coefficients={
            "avg_mastery": -59.55547147451526,
            "recent_attempt_score": 0.21976016089345762,
            "time_spent_minutes": 0.5791920216778657,
            "attempts_last_week": -1.5142346533763074,
            "question_difficulty": -49.905751732403324,
        },
    )
    return LinearRegressionModel(weights=weights)


def train_regression_weights(rows: Iterable[Dict[str, float]]) -> Optional[RegressionWeights]:
    rows = list(rows)
    feature_names = [
        "avg_mastery",
        "recent_attempt_score",
        "time_spent_minutes",
        "attempts_last_week",
        "question_difficulty",
    ]
    #if the data is insufficient for training return none, mostly for debugging
    if len(rows) < 5:
        return None

    try:
        import numpy as np
    except ImportError:
        return None

    X = np.array([[row.get(name, 0.0) for name in feature_names] for row in rows], dtype=float)
    y = np.array([row["target_score"] for row in rows], dtype=float)

    try:
        from sklearn.linear_model import LinearRegression # type: ignore

        model = LinearRegression().fit(X, y)
        intercept = float(model.intercept_)
        coef = model.coef_
    except Exception:
        Xb = np.column_stack([np.ones(len(X)), X])
        coef_all, *_ = np.linalg.lstsq(Xb, y, rcond=None)
        intercept = float(coef_all[0])
        coef = coef_all[1:]

    weights = {name: float(w) for name, w in zip(feature_names, coef)}
    return RegressionWeights(intercept=intercept, coefficients=weights)

