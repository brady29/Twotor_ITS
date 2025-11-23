"""Analytics utilities for the TwoTor ITS."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List

from .models import Attempt, Quiz, User


def gradebook_rows(
    attempts: Iterable[Attempt], users: Dict[str, User], quizzes: Dict[str, Quiz]
) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for attempt in attempts:
        user = users.get(attempt.user_id)
        quiz = quizzes.get(attempt.quiz_id)
        if not user or not quiz:
            continue
        rows.append(
            {
                "user_id": user.user_id,
                "student": user.name,
                "quiz": quiz.title,
                "score": f"{attempt.score:.1f}",
                "correct": f"{attempt.correct_count}/{attempt.total_questions}",
                "time_seconds": str(attempt.time_taken_seconds),
            }
        )
    return rows


def export_gradebook_csv(path: Path, rows: List[Dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("user_id,student,quiz,score,correct,time_seconds\\n", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def mastery_snapshot(progress: Dict[str, float]) -> Dict[str, float]:
    return {skill: round(value, 3) for skill, value in progress.items()}


def attempt_velocity(attempts: Iterable[Attempt], window: int = 7) -> float:
    # For demo we simply return avg attempts per quiz (bounded).
    attempt_list = list(attempts)
    if not attempt_list:
        return 0.0
    quizzes = {attempt.quiz_id for attempt in attempt_list}
    return round(len(attempt_list) / max(len(quizzes), 1), 2)


def quiz_item_feedback(quiz: Quiz, attempt: Attempt) -> List[str]:
    lines: List[str] = []
    for idx, question in enumerate(quiz.questions):
        chosen = attempt.answers[idx]
        is_correct = chosen == question.correct_choice
        options = "; ".join(
            f"{i + 1}. {option}" for i, option in enumerate(question.choices)
        )
        lines.append(
            f"Q{idx + 1}: {question.prompt}\\n"
            f"Choices: {options}\\n"
            f"Selected: {chosen + 1} - {'Correct' if is_correct else 'Incorrect'} "
            f"(Answer: {question.correct_choice + 1})\\n"
        )
    return lines
