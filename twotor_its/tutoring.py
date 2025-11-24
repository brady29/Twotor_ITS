"""Top-level tutoring system orchestration."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Dict, List

from .analytics import (
    attempt_velocity,
    export_gradebook_csv,
    gradebook_rows,
    mastery_snapshot,
    quiz_item_feedback,
)
from .bkt import BKTModel, default_bkt_model
from .helpdesk import Helpdesk
from .models import Attempt, Course, Lesson, LessonActivity, ProgressRecord, Quiz, User, UserRole
from .regression import LinearRegressionModel, default_regression_model
from .storage import Storage


class TutoringSystem:
    NAV_ITEMS = [
        "dashboard",
        "quizzes",
        "analytics",
        "help",
        "profile",
        "settings",
    ]

    def __init__(self, data_dir: str | Path):
        data_path = Path(data_dir)
        self.storage = Storage(data_path)
        self.users: Dict[str, User] = self.storage.load_users()
        self.courses: Dict[str, Course] = self.storage.load_courses()
        self.attempts: List[Attempt] = self.storage.load_attempts()
        self.progress_records: List[ProgressRecord] = self.storage.load_progress()
        self.lesson_activity: List[LessonActivity] = self.storage.load_lesson_activity()
        self.helpdesk = Helpdesk(self.storage.load_help_tickets())
        self.regression: LinearRegressionModel = default_regression_model()
        self._mastery_cache: Dict[str, BKTModel] = {}
        self._quiz_index: Dict[str, Quiz] = self._build_quiz_index()
        self._lesson_index: Dict[str, Lesson] = self._build_lesson_index()

    # region lookup helpers
    def _build_quiz_index(self) -> Dict[str, Quiz]:
        quizzes: Dict[str, Quiz] = {}
        for course in self.courses.values():
            for module in course.modules:
                for quiz in module.quizzes:
                    quizzes[quiz.quiz_id] = quiz
        return quizzes

    def _build_lesson_index(self) -> Dict[str, Lesson]:
        lessons: Dict[str, Lesson] = {}
        for course in self.courses.values():
            for module in course.modules:
                for lesson in getattr(module, "lessons", []):
                    lessons[lesson.lesson_id] = lesson
        return lessons

    def get_quiz(self, quiz_id: str) -> Quiz:
        if quiz_id not in self._quiz_index:
            raise KeyError(f"Quiz {quiz_id} not found")
        return self._quiz_index[quiz_id]

    def get_user(self, user_id: str) -> User:
        if user_id not in self.users:
            raise KeyError(f"User {user_id} not found")
        return self.users[user_id]

    # endregion

    # region dashboards
    def student_dashboard(self, user_id: str) -> Dict:
        student = self.get_user(user_id)
        if student.role != UserRole.STUDENT:
            raise ValueError("Dashboard is only available to students")
        mastery = mastery_snapshot(self._get_bkt(user_id).dump_mastery())
        recent = [attempt for attempt in self.attempts if attempt.user_id == user_id][-3:]
        prediction = self._predict_next_score(user_id)
        lesson_activity = [entry for entry in self.lesson_activity if entry.user_id == user_id]
        lessons = []
        completed_lessons = {entry.lesson_id for entry in lesson_activity}
        for lesson in self.list_lessons():
            lessons.append(
                {
                    "lesson_id": lesson.lesson_id,
                    "title": lesson.title,
                    "skill": lesson.skill,
                    "estimated_minutes": lesson.estimated_minutes,
                    "summary": lesson.summary,
                    "completed": lesson.lesson_id in completed_lessons,
                }
            )
        return {
            "user": student.to_dict(),
            "navigation": self.NAV_ITEMS,
            "mastery": mastery,
            "recent_attempts": [attempt.to_dict() for attempt in recent],
            "predicted_next_score": round(prediction, 1) if prediction is not None else None,
            "lessons": lessons,
            "lesson_activity_minutes": sum(entry.minutes_spent for entry in lesson_activity),
        }

    def teacher_dashboard(self, user_id: str) -> Dict:
        teacher = self.get_user(user_id)
        if teacher.role != UserRole.TEACHER:
            raise ValueError("Dashboard is only available to teachers")
        relevant_courses = [
            course for course in self.courses.values() if course.instructor_id == teacher.user_id
        ]
        roster_ids = {
            student_id
            for course in relevant_courses
            for student_id in getattr(course, "student_ids", [])
        }
        if not roster_ids:
            roster_ids = {
                user.user_id for user in self.users.values() if user.role == UserRole.STUDENT
            }
        roster = [
            self.users[user_id]
            for user_id in roster_ids
            if user_id in self.users and self.users[user_id].role == UserRole.STUDENT
        ]
        roster_details = []
        for student in sorted(roster, key=lambda u: u.name):
            student_attempts = [attempt for attempt in self.attempts if attempt.user_id == student.user_id]
            avg_score = round(mean([attempt.score for attempt in student_attempts]), 1) if student_attempts else None
            predicted = self._predict_next_score(student.user_id)
            roster_details.append(
                {
                    "user_id": student.user_id,
                    "name": student.name,
                    "attempts": len(student_attempts),
                    "average_score": avg_score,
                    "predicted_score": round(predicted, 1) if predicted is not None else None,
                    "last_quiz": student_attempts[-1].quiz_id if student_attempts else None,
                }
            )
        quiz_map = self._quiz_index
        rows = gradebook_rows(self.attempts, self.users, quiz_map)
        difficulty_breakdown = self._difficulty_breakdown(roster_ids)
        at_risk = [
            student for student in roster_details if student["predicted_score"] is not None and student["predicted_score"] < 50
        ]
        mastery_agg: Dict[str, List[float]] = {}
        for record in self.progress_records:
            if record.user_id in roster_ids:
                mastery_agg.setdefault(record.skill, []).append(record.mastered_probability)
        class_mastery = {
            skill: round(mean(values) * 100, 1) if values else 0.0 for skill, values in mastery_agg.items()
        }
        student_mastery_scores = []
        for student in roster:
            mastery_dump = self._get_bkt(student.user_id).dump_mastery()
            mastery_values = list(mastery_dump.values())
            avg_mastery = mean(mastery_values) if mastery_values else 0.0
            student_mastery_scores.append(
                {
                    "user_id": student.user_id,
                    "name": student.name,
                    "mastery_score": round(avg_mastery * 100, 1),
                    "mastery": {
                        skill: round(probability * 100, 1) for skill, probability in mastery_dump.items()
                    },
                }
            )
        student_mastery_scores.sort(key=lambda entry: entry["mastery_score"], reverse=True)
        help_requests = [
            {
                "ticket_id": ticket.ticket_id,
                "student": self.users.get(ticket.user_id, User(ticket.user_id, ticket.user_id, UserRole.STUDENT)).name
                if ticket.user_id in self.users
                else ticket.user_id,
                "user_id": ticket.user_id,
                "channel": ticket.channel,
                "question": ticket.question,
                "created_at": ticket.created_at,
                "status": ticket.status,
                "response": ticket.response,
            }
            for ticket in self.helpdesk.dump()
            if ticket.user_id in roster_ids
        ]
        help_requests = sorted(help_requests, key=lambda h: h["created_at"], reverse=True)[:20]
        return {
            "user": teacher.to_dict(),
            "navigation": self.NAV_ITEMS,
            "courses": [course.to_dict() for course in relevant_courses],
            "class_roster": roster_details,
            "at_risk_students": at_risk,
            "gradebook_preview": rows[-5:],
            "attempt_velocity": attempt_velocity(self.attempts),
            "help_requests": help_requests,
            "class_mastery": class_mastery,
            "student_mastery_scores": student_mastery_scores,
            "difficulty_breakdown": difficulty_breakdown,
        }

    # endregion

    # region quiz flow
    def list_quizzes(self) -> List[Dict]:
        return [
            {
                "quiz_id": quiz.quiz_id,
                "title": quiz.title,
                "graded": quiz.graded,
                "time_limit_minutes": quiz.time_limit_minutes,
                "question_count": len(quiz.questions),
            }
            for quiz in self._quiz_index.values()
        ]

    def take_quiz(
        self,
        user_id: str,
        quiz_id: str,
        answers: List[int],
        time_taken_seconds: int,
    ) -> Dict:
        student = self.get_user(user_id)
        quiz = self.get_quiz(quiz_id)
        if len(answers) != len(quiz.questions):
            raise ValueError("Answers length does not match question count")
        correct = 0
        for answer, question in zip(answers, quiz.questions):
            if answer == question.correct_choice:
                correct += 1
        score = (correct / len(quiz.questions)) * 100
        attempt = Attempt(
            user_id=user_id,
            quiz_id=quiz_id,
            answers=answers,
            correct_count=correct,
            total_questions=len(quiz.questions),
            time_taken_seconds=time_taken_seconds,
            score=round(score, 1),
        )
        self.attempts.append(attempt)
        self.storage.save_attempts(self.attempts)
        skill_updates = self._update_mastery(student.user_id, quiz, answers)
        predicted = self._predict_next_score(user_id)
        feedback = quiz_item_feedback(quiz, attempt)
        return {
            "attempt": attempt.to_dict(),
            "skill_updates": skill_updates,
            "prediction": round(predicted, 1) if predicted is not None else None,
            "feedback": feedback,
        }

    def record_lesson_participation(
        self, user_id: str, lesson_id: str, minutes_spent: int = 10
    ) -> Dict:
        student = self.get_user(user_id)
        if student.role != UserRole.STUDENT:
            raise ValueError("Participants must be students")
        if lesson_id not in self._lesson_index:
            raise KeyError(f"Lesson {lesson_id} not found")
        minutes_spent = max(minutes_spent, 1)
        lesson = self._lesson_index[lesson_id]
        model = self._get_bkt(user_id)
        current = model.dump_mastery().get(lesson.skill, 0.0)
        boost = min(0.12, 0.02 * (minutes_spent / max(lesson.estimated_minutes, 5)))
        model.mastery[lesson.skill] = max(0.0, min(1.0, current + boost * (1 - current)))
        self._persist_mastery(user_id)
        activity = LessonActivity(
            user_id=user_id,
            lesson_id=lesson_id,
            minutes_spent=minutes_spent,
            completed_at=datetime.utcnow().isoformat(),
        )
        self.lesson_activity.append(activity)
        self.storage.save_lesson_activity(self.lesson_activity)
        return {
            "lesson": lesson.to_dict(),
            "mastery": mastery_snapshot(self._get_bkt(user_id).dump_mastery()),
        }

    # endregion

    # region analytics + exports
    def export_grades(self, destination: Path) -> Path:
        rows = gradebook_rows(self.attempts, self.users, self._quiz_index)
        export_gradebook_csv(destination, rows)
        return destination

    # endregion

    # region help
    def request_help(self, user_id: str, channel: str, question: str) -> Dict:
        if channel not in {"appointment", "assignment"}:
            raise ValueError("channel must be 'appointment' or 'assignment'")
        ticket = self.helpdesk.create_ticket(user_id, channel, question)
        self.storage.save_help_tickets(self.helpdesk.dump())
        return asdict(ticket)

    # endregion

    # region lessons + profiles
    def list_lessons(self) -> List[Lesson]:
        return list(self._lesson_index.values())

    def student_profile(self, user_id: str) -> Dict:
        student = self.get_user(user_id)
        if student.role != UserRole.STUDENT:
            raise ValueError("Profiles are only available for students")
        attempts = [attempt for attempt in self.attempts if attempt.user_id == user_id]
        mastery = mastery_snapshot(self._get_bkt(user_id).dump_mastery())
        avg_score = round(mean([a.score for a in attempts]), 1) if attempts else None
        lesson_activity = [entry for entry in self.lesson_activity if entry.user_id == user_id]
        lessons_completed = {entry.lesson_id for entry in lesson_activity}
        help_requests = [ticket for ticket in self.helpdesk.dump() if ticket.user_id == user_id]
        prediction = self._predict_next_score(user_id)
        return {
            "user": student.to_dict(),
            "mastery": mastery,
            "predicted_next_score": round(prediction, 1) if prediction is not None else None,
            "attempts": [attempt.to_dict() for attempt in attempts[-10:]],
            "attempt_stats": {
                "total_attempts": len(attempts),
                "average_score": avg_score,
                "latest_quiz": attempts[-1].quiz_id if attempts else None,
                "recent_trend": [a.score for a in attempts[-5:]],
            },
            "lesson_progress": {
                "completed_count": len(lessons_completed),
                "total_minutes": sum(entry.minutes_spent for entry in lesson_activity),
                "recent": [asdict(entry) for entry in lesson_activity[-5:]],
            },
            "help_requests": [asdict(ticket) for ticket in help_requests[-5:]],
        }

    # endregion

    # region internal helpers
    def _get_bkt(self, user_id: str) -> BKTModel:
        if user_id in self._mastery_cache:
            return self._mastery_cache[user_id]
        model = default_bkt_model()
        mastery = {
            record.skill: record.mastered_probability
            for record in self.progress_records
            if record.user_id == user_id
        }
        if mastery:
            model.load_mastery(mastery)
        self._mastery_cache[user_id] = model
        return model

    def _update_mastery(self, user_id: str, quiz: Quiz, answers: List[int]) -> Dict[str, float]:
        model = self._get_bkt(user_id)
        updates: Dict[str, float] = {}
        for answer, question in zip(answers, quiz.questions):
            mastered = model.update(question.skill, answer == question.correct_choice)
            updates[question.skill] = round(mastered, 3)
        self._persist_mastery(user_id)
        return updates

    def _persist_mastery(self, user_id: str) -> None:
        model = self._get_bkt(user_id)
        mastery_dump = model.dump_mastery()
        other_records = [record for record in self.progress_records if record.user_id != user_id]
        for skill, value in mastery_dump.items():
            other_records.append(
                ProgressRecord(
                    user_id=user_id,
                    skill=skill,
                    mastered_probability=round(value, 4),
                )
            )
        self.progress_records = other_records
        self.storage.save_progress(self.progress_records)

    def _difficulty_breakdown(self, roster_ids: set[str]) -> Dict[str, float]:
        buckets: Counter = Counter({"Easy": 0, "Medium": 0, "Hard": 0})
        for attempt in self.attempts:
            if attempt.user_id not in roster_ids:
                continue
            quiz = self._quiz_index.get(attempt.quiz_id)
            if not quiz:
                continue
            for question in quiz.questions:
                if question.difficulty <= 1:
                    buckets["Easy"] += 1
                elif question.difficulty == 2:
                    buckets["Medium"] += 1
                else:
                    buckets["Hard"] += 1
        total = sum(buckets.values())
        if total == 0:
            return {key: 0.0 for key in buckets}
        return {key: round((value / total) * 100, 1) for key, value in buckets.items()}

    def _predict_next_score(self, user_id: str) -> float | None:
        attempts = [attempt for attempt in self.attempts if attempt.user_id == user_id]
        if not attempts:
            return None
        quiz = self.get_quiz(attempts[-1].quiz_id)
        mastery_values = list(self._get_bkt(user_id).dump_mastery().values())
        features = {
            "avg_mastery": mean(mastery_values) if mastery_values else 0.3,
            "recent_attempt_score": attempts[-1].score,
            "time_spent_minutes": attempts[-1].time_taken_seconds / 60,
            "attempts_last_week": min(len(attempts[-7:]), 7),
            "question_difficulty": mean(q.difficulty for q in quiz.questions),
        }
        return self.regression.predict_clipped(features)

    # endregion
