from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from twotor_its import TutoringSystem
from twotor_its.models import UserRole
from twotor_its.policy import UsernamePolicy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="TwoTor Intelligent Tutoring System CLI (consistent navigation: dashboard/quizzes/analytics/help/profile/settings)."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).parent / "data",
        help="Directory containing content and state JSON files.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    dashboard = sub.add_parser("dashboard", help="Show dashboard for a user.")
    dashboard.add_argument("--user", required=True, help="User ID.")

    quizzes = sub.add_parser("list-quizzes", help="List available quizzes.")
    quizzes.add_argument("--graded-only", action="store_true", help="Show only graded quizzes.")

    take = sub.add_parser("take-quiz", help="Submit answers for a quiz.")
    take.add_argument("--user", required=True, help="Student ID.")
    take.add_argument("--quiz", required=True, help="Quiz ID.")
    take.add_argument(
        "--answers",
        nargs="+",
        type=int,
        required=True,
        help="Space separated answer indices (1-based as displayed to students).",
    )
    take.add_argument(
        "--time-seconds",
        type=int,
        default=300,
        help="Time spent on quiz in seconds.",
    )

    export = sub.add_parser("export-grades", help="Export gradebook to CSV.")
    export.add_argument(
        "--dest",
        type=Path,
        default=Path("exports/gradebook.csv"),
        help="Destination CSV path.",
    )

    helpdesk_cmd = sub.add_parser("help", help="Route help via appointment or assignment channel.")
    helpdesk_cmd.add_argument("--user", required=True, help="User ID.")
    helpdesk_cmd.add_argument(
        "--channel",
        choices=["appointment", "assignment"],
        required=True,
        help="Help path requested by the participant.",
    )
    helpdesk_cmd.add_argument("--question", required=True, help="Question or issue.")

    policy_cmd = sub.add_parser("validate-username", help="Validate usernames for restricted words.")
    policy_cmd.add_argument("username", help="Username to evaluate.")

    nav_cmd = sub.add_parser("nav", help="Display the consistent navigation menu.")

    return parser


def load_system(data_dir: Path) -> TutoringSystem:
    return TutoringSystem(data_dir=data_dir)


def command_dashboard(system: TutoringSystem, user_id: str) -> None:
    user = system.get_user(user_id)
    if user.role == UserRole.STUDENT:
        payload = system.student_dashboard(user_id)
    else:
        payload = system.teacher_dashboard(user_id)
    print(json.dumps(payload, indent=2))


def command_list_quizzes(system: TutoringSystem, graded_only: bool) -> None:
    quizzes = system.list_quizzes()
    if graded_only:
        quizzes = [quiz for quiz in quizzes if quiz["graded"]]
    print(json.dumps(quizzes, indent=2))


def command_take_quiz(
    system: TutoringSystem, user: str, quiz: str, answers: List[int], time_seconds: int
) -> None:
    zero_indexed = [choice - 1 for choice in answers]
    payload = system.take_quiz(user, quiz, zero_indexed, time_seconds)
    print(json.dumps(payload, indent=2))


def command_export(system: TutoringSystem, dest: Path) -> None:
    export_path = system.export_grades(dest)
    print(f"Gradebook exported to {export_path.resolve()}")


def command_help(system: TutoringSystem, user: str, channel: str, question: str) -> None:
    ticket = system.request_help(user, channel, question)
    print(json.dumps(ticket, indent=2))


def command_validate_username(username: str) -> None:
    policy = UsernamePolicy()
    result = policy.validate(username)
    print(json.dumps({"username": result.username, "valid": result.valid, "message": result.message}, indent=2))


def command_nav(system: TutoringSystem) -> None:
    print(json.dumps({"navigation": system.NAV_ITEMS}, indent=2))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    system = load_system(args.data_dir)

    if args.command == "dashboard":
        command_dashboard(system, args.user)
    elif args.command == "list-quizzes":
        command_list_quizzes(system, args.graded_only)
    elif args.command == "take-quiz":
        command_take_quiz(system, args.user, args.quiz, args.answers, args.time_seconds)
    elif args.command == "export-grades":
        command_export(system, args.dest)
    elif args.command == "help":
        command_help(system, args.user, args.channel, args.question)
    elif args.command == "validate-username":
        command_validate_username(args.username)
    elif args.command == "nav":
        command_nav(system)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
