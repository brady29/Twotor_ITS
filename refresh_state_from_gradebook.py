#!/usr/bin/env python3
"""Utility to rebuild data/state.json attempts from the gradebook CSV."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from twotor_its.bkt import BKTModel, default_bkt_model

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATE_PATH = DATA_DIR / "state.json"
CONTENT_PATH = DATA_DIR / "sample_content.json"
GRADEBOOK_PATH = BASE_DIR / "exports" / "gradebook.csv"

QUIZ_TITLE_TO_ID: Dict[str, str] = {
    "Precalculus Diagnostic 1": "quiz-pre-01",
    "Precalculus Diagnostic 2": "quiz-pre-02",
    "Precalculus Diagnostic 3": "quiz-pre-03",
    "Functions and Graphs": "quiz-pre-01",
    "Exponents and Logarithms": "quiz-pre-02",
    "Trig Refresher": "quiz-pre-03",
    "Understanding Limits": "quiz-calc-01",
    "Continuity and Discontinuities": "quiz-calc-02",
    "Limits and Continuity 1": "quiz-calc-01",
    "Limits and Continuity 2": "quiz-calc-02",
    "Limits and Continuity 3": "quiz-calc-03",
    "Derivative Definition": "quiz-calc-04",
    "Rules and Shortcuts": "quiz-calc-05",
    "Derivatives 1": "quiz-calc-04",
    "Derivatives 2": "quiz-calc-05",
    "Derivatives 3": "quiz-calc-06",
    "Optimization": "quiz-calc-07",
    "Related Rates": "quiz-calc-08",
    "Applications 1": "quiz-calc-07",
    "Applications 2": "quiz-calc-08",
    "Applications 3": "quiz-calc-09",
    "Antiderivatives Basics": "quiz-calc-10",
    "Definite Integrals and Area": "quiz-calc-10",
    "Integrals 1": "quiz-calc-10",
    "Integrals 2": "quiz-calc-11",
    "Integrals 3": "quiz-calc-12",
    "Applications of Integrals": "quiz-calc-12",
}

PATTERN_MAP: Dict[str, List[bool]] = {
    "ace": [True, True, True],
    "strong": [True, True, False],
    "steady": [True, False, True],
    "developing": [True, False, False],
    "struggle": [False, True, False],
    "fail": [False, False, False],
}


def load_quizzes() -> Dict[str, Dict]:
    content = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    quizzes: Dict[str, Dict] = {}
    for course in content.get("courses", []):
        for module in course.get("modules", []):
            for quiz in module.get("quizzes", []):
                quizzes[quiz["quiz_id"]] = quiz
    return quizzes


def pick_pattern(score: float) -> str:
    if score >= 90:
        return "ace"
    if score >= 75:
        return "strong"
    if score >= 55:
        return "steady"
    if score >= 40:
        return "developing"
    if score >= 20:
        return "struggle"
    return "fail"


def answers_for_quiz(quiz: Dict, pattern_key: str) -> List[int]:
    pattern = PATTERN_MAP[pattern_key]
    questions = quiz["questions"]
    if len(pattern) != len(questions):
        if len(pattern) < len(questions):
            # pad by repeating final behavior
            pattern = pattern + [pattern[-1]] * (len(questions) - len(pattern))
        else:
            pattern = pattern[: len(questions)]
    answers: List[int] = []
    for is_correct, question in zip(pattern, questions):
        correct_choice = question["correct_choice"]
        if is_correct:
            answers.append(correct_choice)
        else:
            answers.append((correct_choice + 1) % len(question["choices"]))
    return answers


def rebuild_attempts(quizzes: Dict[str, Dict]) -> List[Dict]:
    rows = list(csv.DictReader(GRADEBOOK_PATH.open(encoding="utf-8")))
    content = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    valid_users = {user["user_id"] for user in content.get("users", []) if user["role"] == "student"}

    attempts: List[Dict] = []
    for row in rows:
        user_id = row["user_id"]
        if user_id not in valid_users:
            continue
        quiz_title = row["quiz"]
        quiz_id = QUIZ_TITLE_TO_ID.get(quiz_title)
        if not quiz_id:
            print(f"Skipping row for {user_id} with unknown quiz title '{quiz_title}'")
            continue
        quiz = quizzes[quiz_id]
        score = float(row["score"])
        pattern_key = pick_pattern(score)
        answers = answers_for_quiz(quiz, pattern_key)
        correct_text = row["correct"]
        try:
            correct_value, total_value = (int(part) for part in correct_text.split("/"))
        except ValueError:
            correct_value, total_value = 0, len(quiz["questions"])
        time_seconds = int(float(row["time_seconds"]))
        attempts.append(
            {
                "user_id": user_id,
                "quiz_id": quiz_id,
                "answers": answers,
                "correct_count": correct_value,
                "total_questions": total_value,
                "time_taken_seconds": time_seconds,
                "score": score,
            }
        )
    return attempts


def compute_progress(quizzes: Dict[str, Dict], attempts: List[Dict]) -> List[Dict]:
    attempts_by_user: Dict[str, List[Dict]] = defaultdict(list)
    for attempt in attempts:
        attempts_by_user[attempt["user_id"]].append(attempt)
    records: List[Dict] = []
    for user_id, user_attempts in attempts_by_user.items():
        model: BKTModel = default_bkt_model()
        for attempt in user_attempts:
            quiz = quizzes[attempt["quiz_id"]]
            for answer, question in zip(attempt["answers"], quiz["questions"]):
                model.update(question["skill"], answer == question["correct_choice"])
        mastery = model.dump_mastery()
        for skill, value in mastery.items():
            records.append(
                {
                    "user_id": user_id,
                    "skill": skill,
                    "mastered_probability": round(value, 4),
                }
            )
    return records


def main() -> None:
    quizzes = load_quizzes()
    attempts = rebuild_attempts(quizzes)
    progress = compute_progress(quizzes, attempts)

    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    state["attempts"] = attempts
    state["progress"] = progress
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print(f"Updated {STATE_PATH} with {len(attempts)} attempts and {len(progress)} progress records.")


if __name__ == "__main__":
    main()
