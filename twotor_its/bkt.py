

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class BKTParams:
    learn: float
    forget: float
    guess: float
    slip: float


class BKTModel:


    def __init__(self, parameters: Dict[str, BKTParams], priors: Dict[str, float]):
        self.parameters = parameters
        self.mastery = {skill: priors.get(skill, 0.3) for skill in parameters}

    def load_mastery(self, mastery: Dict[str, float]) -> None:
        for skill, value in mastery.items():
            if skill in self.mastery:
                self.mastery[skill] = value

    def dump_mastery(self) -> Dict[str, float]:
        return dict(self.mastery)

    def predict_mastery(self, skill: str) -> float:
        return self.mastery.get(skill, 0.0)

    def update(self, skill: str, is_correct: bool) -> float:
        params = self.parameters.get(skill)
        if not params:
            return 0.0
        prior = self.mastery.get(skill, 0.3)
        if is_correct:
            num = prior * (1 - params.slip)
            den = num + (1 - prior) * params.guess
        else:
            num = prior * params.slip
            den = num + (1 - prior) * (1 - params.guess)
        posterior = num / den if den else prior
        learned = posterior + (1 - posterior) * params.learn
        mastered = learned * (1 - params.forget) + (1 - learned) * params.learn
        self.mastery[skill] = max(0.0, min(1.0, mastered))
        return self.mastery[skill]


def default_bkt_model() -> BKTModel:
    params = {
        "precalculus": BKTParams(learn=0.14, forget=0.02, guess=0.18, slip=0.1),
        "calculus": BKTParams(learn=0.16, forget=0.02, guess=0.16, slip=0.1),
    }
    priors = {skill: 0.35 for skill in params}
    return BKTModel(parameters=params, priors=priors)
