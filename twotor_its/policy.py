"""Input validation policies inspired by post-mortem findings."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


@dataclass
class UsernameCheckResult:
    username: str
    valid: bool
    message: str


class UsernamePolicy:
    def __init__(self, banned_words: List[str] | None = None):
        self.banned_words = banned_words or ["vile", "evil", "toxic", "nsfw", "curse"]
        self.patterns = [re.compile(word, re.IGNORECASE) for word in self.banned_words]

    def validate(self, username: str) -> UsernameCheckResult:
        if not username:
            return UsernameCheckResult(username, False, "Username cannot be empty.")
        if len(username) < 3:
            return UsernameCheckResult(username, False, "Username must be at least 3 characters.")
        for pattern, word in zip(self.patterns, self.banned_words):
            if pattern.search(username):
                return UsernameCheckResult(
                    username,
                    False,
                    f"Username rejected: contains restricted word '{word}'.",
                )
        if not re.match(r"^[A-Za-z0-9_.-]+$", username):
            return UsernameCheckResult(
                username,
                False,
                "Username may only include letters, digits, hyphen, underscore, or dot.",
            )
        return UsernameCheckResult(username, True, "Username accepted.")
