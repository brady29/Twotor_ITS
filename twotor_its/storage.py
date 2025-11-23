"""JSON backed storage helpers for the TwoTor ITS."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .helpdesk import HelpTicket
from .models import Attempt, Course, LessonActivity, ProgressRecord, User


class Storage:
    """Simple JSON storage for demo purposes."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.content_path = self.data_dir / "sample_content.json"
        self.state_path = self.data_dir / "state.json"

        if not self.content_path.exists():
            raise FileNotFoundError(
                f"Expected seed content at {self.content_path}. Did you run setup?"
            )
        if not self.state_path.exists():
            self._initialize_state()

    # region public loaders
    def load_users(self) -> Dict[str, User]:
        return {
            item["user_id"]: User.from_dict(item)
            for item in self._read_content_section("users")
        }

    def load_courses(self) -> Dict[str, Course]:
        return {
            item["course_id"]: Course.from_dict(item)
            for item in self._read_content_section("courses")
        }

    def load_attempts(self) -> List[Attempt]:
        return [
            Attempt.from_dict(item) for item in self._read_state().get("attempts", [])
        ]

    def save_attempts(self, attempts: List[Attempt]) -> None:
        state = self._read_state()
        state["attempts"] = [attempt.to_dict() for attempt in attempts]
        self._write_state(state)

    def load_progress(self) -> List[ProgressRecord]:
        return [
            ProgressRecord.from_dict(item)
            for item in self._read_state().get("progress", [])
        ]

    def save_progress(self, progress: List[ProgressRecord]) -> None:
        state = self._read_state()
        state["progress"] = [record.to_dict() for record in progress]
        self._write_state(state)

    def load_help_tickets(self) -> List[HelpTicket]:
        return [
            HelpTicket.from_dict(item) for item in self._read_state().get("help_tickets", [])
        ]

    def save_help_tickets(self, tickets: List[HelpTicket]) -> None:
        state = self._read_state()
        state["help_tickets"] = [ticket.to_dict() for ticket in tickets]
        self._write_state(state)

    def load_lesson_activity(self) -> List[LessonActivity]:
        return [
            LessonActivity.from_dict(item)
            for item in self._read_state().get("lesson_activity", [])
        ]

    def save_lesson_activity(self, activity: List[LessonActivity]) -> None:
        state = self._read_state()
        state["lesson_activity"] = [entry.to_dict() for entry in activity]
        self._write_state(state)

    # endregion

    def _initialize_state(self) -> None:
        state = {
            "attempts": [],
            "progress": [],
            "notifications": [],
            "help_tickets": [],
            "lesson_activity": [],
        }
        self._write_state(state)

    def _read_content_section(self, key: str):
        content = json.loads(self.content_path.read_text(encoding="utf-8"))
        return content.get(key, [])

    def _read_state(self) -> Dict:
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def _write_state(self, payload: Dict) -> None:
        self.state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
