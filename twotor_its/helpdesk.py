"""Help desk routing for appointment vs assignment help."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List


@dataclass
class HelpTicket:
    ticket_id: str
    user_id: str
    channel: str  
    question: str
    created_at: str
    status: str = "open"
    response: str | None = None

    def to_dict(self) -> dict:
        return {
            "ticket_id": self.ticket_id,
            "user_id": self.user_id,
            "channel": self.channel,
            "question": self.question,
            "created_at": self.created_at,
            "status": self.status,
            "response": self.response,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HelpTicket":
        return cls(**data)


class Helpdesk:
    def __init__(self, tickets: List[HelpTicket] | None = None):
        self.tickets: List[HelpTicket] = tickets or []

    def create_ticket(self, user_id: str, channel: str, question: str) -> HelpTicket:
        ticket = HelpTicket(
            ticket_id=f"HELP-{len(self.tickets) + 1:04d}",
            user_id=user_id,
            channel=channel,
            question=question,
            created_at=datetime.utcnow().isoformat(),
            response=self._auto_response(channel),
        )
        ticket.status = "responded"
        self.tickets.append(ticket)
        return ticket

    def dump(self) -> List[HelpTicket]:
        return list(self.tickets)

    def _auto_response(self, channel: str) -> str:
        if channel == "appointment":
            slot = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d 10:00")
            return f"Appointment reserved for {slot} with Dr. Antonie"
        return "Please review materials and your instructor will get back to you shortly"
