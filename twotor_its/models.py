'''This is the datamodel for the twotor inteligent system, the modules are:
- User
- Question
- Quiz
- Lesson
- Module
- Course
- Attempt
- ProgressRecord
- LessonActivity
'''
from __future__ import annotations



from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, List, Optional


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"


@dataclass
class User:
    user_id: str
    name: str
    role: UserRole
    email: Optional[str] = None

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["role"] = self.role.value
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> "User":
        return cls(
            user_id=data["user_id"],
            name=data["name"],
            role=UserRole(data["role"]),
            email=data.get("email"),
        )


@dataclass
class Question:
    question_id: str
    prompt: str
    choices: List[str]
    correct_choice: int
    skill: str
    difficulty: int = 1

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Question":
        return cls(**data)


@dataclass
class Quiz:
    quiz_id: str
    title: str
    questions: List[Question]
    graded: bool = False
    time_limit_minutes: Optional[int] = None

    def to_dict(self) -> Dict:
        return {
            "quiz_id": self.quiz_id,
            "title": self.title,
            "graded": self.graded,
            "time_limit_minutes": self.time_limit_minutes,
            "questions": [q.to_dict() for q in self.questions],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Quiz":
        return cls(
            quiz_id=data["quiz_id"],
            title=data["title"],
            questions=[Question.from_dict(q) for q in data["questions"]],
            graded=data.get("graded", False),
            time_limit_minutes=data.get("time_limit_minutes"),
        )


@dataclass
class Lesson:
    lesson_id: str
    title: str
    skill: str
    summary: str
    content: str
    estimated_minutes: int = 10

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Lesson":
        return cls(**data)


@dataclass
class Module:
    module_id: str
    title: str
    description: str
    quizzes: List[Quiz] = field(default_factory=list)
    lessons: List[Lesson] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "module_id": self.module_id,
            "title": self.title,
            "description": self.description,
            "quizzes": [q.to_dict() for q in self.quizzes],
            "lessons": [l.to_dict() for l in self.lessons],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Module":
        return cls(
            module_id=data["module_id"],
            title=data["title"],
            description=data["description"],
            quizzes=[Quiz.from_dict(q) for q in data.get("quizzes", [])],
            lessons=[Lesson.from_dict(l) for l in data.get("lessons", [])],
        )


@dataclass
class Course:
    course_id: str
    title: str
    instructor_id: str
    student_ids: List[str] = field(default_factory=list)
    modules: List[Module] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "course_id": self.course_id,
            "title": self.title,
            "instructor_id": self.instructor_id,
            "student_ids": self.student_ids,
            "modules": [m.to_dict() for m in self.modules],
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Course":
        return cls(
            course_id=data["course_id"],
            title=data["title"],
            instructor_id=data["instructor_id"],
            student_ids=data.get("student_ids", []),
            modules=[Module.from_dict(m) for m in data.get("modules", [])],
        )


@dataclass
class Attempt:
    user_id: str
    quiz_id: str
    answers: List[int]
    correct_count: int
    total_questions: int
    time_taken_seconds: int
    score: float

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "Attempt":
        return cls(**data)


@dataclass
class ProgressRecord:
    user_id: str
    skill: str
    mastered_probability: float

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "ProgressRecord":
        return cls(**data)


@dataclass
class LessonActivity:
    user_id: str
    lesson_id: str
    minutes_spent: int
    completed_at: str

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "LessonActivity":
        return cls(**data)
