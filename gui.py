from __future__ import annotations

import argparse
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk
from math import cos, sin, pi

from twotor_its import TutoringSystem
from twotor_its.models import Lesson, Quiz, UserRole


class QuizWindow(tk.Toplevel):
    """Step-through quiz view for students."""

    def __init__(self, parent, quiz: Quiz, on_complete):
        super().__init__(parent)
        self.quiz = quiz
        self.on_complete = on_complete
        self.title(f"{quiz.title} - Practice")
        self.geometry("600x400")

        self.question_index = 0
        self.answers: list[int] = []
        self.choice_var = tk.IntVar(value=-1)
        self.status_var = tk.StringVar(value="Select an answer to continue.")

        self.prompt_label = ttk.Label(self, text="", wraplength=560, font=("Segoe UI", 12, "bold"))
        self.prompt_label.pack(pady=10)

        self.choice_frame = ttk.Frame(self)
        self.choice_frame.pack(fill="both", expand=True)

        self.progress_label = ttk.Label(self, text="")
        self.progress_label.pack(pady=5)
        self.progress_bar = ttk.Progressbar(self, mode="determinate", maximum=len(self.quiz.questions))
        self.progress_bar.pack(fill="x", padx=20, pady=4)

        self.next_button = ttk.Button(self, text="Next", command=self._record_answer)
        self.next_button.pack(pady=10)

        self.status_label = ttk.Label(self, textvariable=self.status_var, foreground="#444")
        self.status_label.pack(pady=4)

        self.bind("<Key-1>", lambda _: self._set_choice(0))
        self.bind("<Key-2>", lambda _: self._set_choice(1))
        self.bind("<Key-3>", lambda _: self._set_choice(2))
        self.bind("<Key-4>", lambda _: self._set_choice(3))

        self._render_question()

    def _render_question(self) -> None:
        question = self.quiz.questions[self.question_index]
        self.choice_var.set(-1)
        self.prompt_label.config(text=f"Q{self.question_index + 1}: {question.prompt}")

        for widget in self.choice_frame.winfo_children():
            widget.destroy()

        for idx, choice in enumerate(question.choices):
            ttk.Radiobutton(
                self.choice_frame,
                text=f"{idx + 1}. {choice}",
                variable=self.choice_var,
                value=idx,
            ).pack(anchor="w", pady=2)

        self.progress_label.config(
            text=f"Question {self.question_index + 1} of {len(self.quiz.questions)}"
        )
        self.progress_bar['value'] = self.question_index
        self.next_button.config(text="Submit" if self.question_index == len(self.quiz.questions) - 1 else "Next")
        self.status_var.set("Select an answer to continue.")

    def _record_answer(self) -> None:
        choice = self.choice_var.get()
        if choice < 0:
            messagebox.showinfo("TwoTor", "Please choose an answer before continuing.")
            return
        self.answers.append(choice)
        if self.question_index == len(self.quiz.questions) - 1:
            self.on_complete(self.answers)
            self.destroy()
            return
        self.question_index += 1
        self._render_question()

    def _set_choice(self, idx: int) -> None:
        self.choice_var.set(idx)
        self.status_var.set(f"Selected option {idx + 1}. Click Next to continue.")

class TwoTorGUI:
    """Tkinter front-end that wraps the TutoringSystem for students and teachers."""

    def __init__(self, root: tk.Tk, system: TutoringSystem):
        self.root = root
        self.system = system
        self.root.title("TwoTor ITS - Classroom Companion")
        self.root.geometry("1120x720")

        self.users = list(system.users.values())
        self.students = [user for user in self.users if user.role == UserRole.STUDENT]
        self.teachers = [user for user in self.users if user.role == UserRole.TEACHER]
        self.selected_user = tk.StringVar()

        self.quiz_map: dict[str, Quiz] = {quiz.quiz_id: quiz for quiz in self.system._quiz_index.values()}
        self.lesson_map: dict[str, Lesson] = {lesson.lesson_id: lesson for lesson in self.system.list_lessons()}
        self.student_mastery_scores: list[dict] = []
        self.lesson_payload: list[dict] = []

        self._build_layout()
        self._build_landing()
        default_user = self.students[0] if self.students else self.users[0]
        self.selected_user.set(default_user.user_id)
        self._show_landing()

    def _build_layout(self) -> None:
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(top_frame, text="User:", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.user_combo = ttk.Combobox(
            top_frame,
            textvariable=self.selected_user,
            values=[user.user_id for user in self.users],
            state="readonly",
            width=22,
        )
        self.user_combo.pack(side="left", padx=5)
        self.user_combo.bind("<<ComboboxSelected>>", lambda _: self.refresh_view())

        self.refresh_button = ttk.Button(top_frame, text="Refresh", command=self.refresh_view)
        self.refresh_button.pack(side="left", padx=5)

        self.help_button = ttk.Button(top_frame, text="Request Help", command=self.request_help)
        self.help_button.pack(side="left", padx=5)

        ttk.Button(top_frame, text="Exit", command=self.root.destroy).pack(side="right")

        separator = ttk.Separator(self.root, orient="horizontal")
        separator.pack(fill="x", padx=10, pady=5)

        self.student_frame = self._build_student_view()
        self.teacher_frame = self._build_teacher_view()
        self.top_frame = top_frame

    def _build_landing(self) -> None:
        self.landing_frame = ttk.Frame(self.root, padding=20)
        ttk.Label(
            self.landing_frame,
            text="Twotor",
            font=("Segoe UI", 28, "bold"),
            foreground="#5c4bff",
        ).pack(pady=6)
        ttk.Label(
            self.landing_frame,
            text="Master Calculus",
            font=("Segoe UI", 14),
        ).pack(pady=2)
        ttk.Label(
            self.landing_frame,
            text="AI-Powered Math Tutoring for High School Students (Grades 10-12)",
            font=("Segoe UI", 10),
        ).pack(pady=2)

        cards = ttk.Frame(self.landing_frame)
        cards.pack(pady=18, fill="x")

        student_card = ttk.Frame(cards, padding=16, relief="groove", borderwidth=2)
        teacher_card = ttk.Frame(cards, padding=16, relief="groove", borderwidth=2)
        student_card.pack(side="left", expand=True, fill="both", padx=10)
        teacher_card.pack(side="left", expand=True, fill="both", padx=10)

        ttk.Label(student_card, text="I'm a Student", font=("Segoe UI", 16, "bold")).pack()
        ttk.Label(student_card, text="Master math concepts from algebra to calculus").pack(pady=4)
        ttk.Button(
            student_card,
            text="Continue as Student",
            command=self._choose_student,
            width=22,
        ).pack(pady=10)

        ttk.Label(teacher_card, text="I'm a Teacher", font=("Segoe UI", 16, "bold")).pack()
        ttk.Label(teacher_card, text="AI-powered insights on student performance").pack(pady=4)
        ttk.Button(
            teacher_card,
            text="Continue as Teacher",
            command=self._choose_teacher,
            width=22,
        ).pack(pady=10)

    def _build_student_view(self) -> ttk.Frame:
        frame = ttk.Frame(self.root)

        content_frame = ttk.Frame(frame)
        content_frame.pack(fill="both", expand=True)

        mastery_frame = ttk.LabelFrame(content_frame, text="Mastery Snapshot")
        mastery_frame.pack(side="left", fill="y", padx=10, pady=5)
        self.mastery_list = tk.Listbox(mastery_frame, width=28, height=8)
        self.mastery_list.pack(fill="both", expand=True, padx=5, pady=5)

        quiz_frame = ttk.LabelFrame(content_frame, text="Quizzes")
        quiz_frame.pack(side="left", fill="y", padx=10, pady=5)
        self.quiz_list = tk.Listbox(quiz_frame, width=40, height=8)
        self.quiz_list.pack(fill="both", expand=True, padx=5, pady=5)
        ttk.Button(quiz_frame, text="Start Quiz", command=self.start_quiz).pack(pady=5)

        lesson_frame = ttk.LabelFrame(content_frame, text="Lessons")
        lesson_frame.pack(side="left", fill="y", padx=10, pady=5)
        self.lesson_list = tk.Listbox(lesson_frame, width=42, height=8)
        self.lesson_list.pack(fill="both", expand=True, padx=5, pady=5)
        ttk.Button(lesson_frame, text="Mark Lesson Read", command=self.mark_lesson_read).pack(pady=5)

        detail_frame = ttk.Frame(content_frame)
        detail_frame.pack(side="left", fill="both", expand=True, padx=5)
        self.prediction_var = tk.StringVar(value="Predicted next score: n/a")
        ttk.Label(detail_frame, textvariable=self.prediction_var).pack(anchor="w", padx=5, pady=5)
        ttk.Label(detail_frame, text="Recent Attempts:").pack(anchor="w", padx=5)
        self.attempts_text = tk.Text(detail_frame, height=8, wrap="word", state="disabled")
        self.attempts_text.pack(fill="both", expand=True, padx=5, pady=5)

        bottom_frame = ttk.LabelFrame(frame, text="Detailed Feedback & Guidance")
        bottom_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.feedback_text = tk.Text(bottom_frame, wrap="word", state="disabled")
        self.feedback_text.pack(fill="both", expand=True, padx=5, pady=5)

        return frame

    def _build_teacher_view(self) -> ttk.Frame:
        frame = ttk.Frame(self.root)

        # Scrollable container for tall dashboards
        container = ttk.Frame(frame)
        container.pack(fill="both", expand=True)
        canvas = tk.Canvas(container, highlightthickness=0)
        v_scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=v_scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")

        inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_frame_config(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_config(event):
            canvas.itemconfigure("all", width=event.width)

        inner.bind("<Configure>", _on_frame_config)
        canvas.bind("<Configure>", _on_canvas_config)

        summary_frame = ttk.Frame(inner)
        summary_frame.pack(fill="x", padx=10, pady=5)
        self.attempt_velocity_var = tk.StringVar(value="Attempt velocity: n/a")
        ttk.Label(summary_frame, textvariable=self.attempt_velocity_var).pack(anchor="w")

        roster_frame = ttk.LabelFrame(inner, text="Class Roster")
        roster_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.roster_tree = ttk.Treeview(
            roster_frame,
            columns=("name", "avg", "pred", "attempts", "last"),
            show="headings",
            height=6,
        )
        for col, heading, width in [
            ("name", "Student", 180),
            ("avg", "Avg", 60),
            ("pred", "Predicted", 80),
            ("attempts", "Attempts", 70),
            ("last", "Last Quiz", 120),
        ]:
            self.roster_tree.heading(col, text=heading)
            self.roster_tree.column(col, width=width, anchor="center")
        self.roster_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.roster_tree.bind("<Double-1>", self._on_student_click)

        risk_frame = ttk.LabelFrame(frame, text="At-Risk (projected < 50%)")
        risk_frame.pack(fill="x", padx=10, pady=5)
        self.at_risk_list = tk.Listbox(risk_frame, height=4)
        self.at_risk_list.pack(fill="both", expand=True, padx=5, pady=5)

        help_frame = ttk.LabelFrame(inner, text="Help Requests")
        help_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.help_tree = ttk.Treeview(
            help_frame,
            columns=("student", "channel", "question", "created", "status"),
            show="headings",
            height=6,
        )
        for col, heading, width, anchor in [
            ("student", "Student", 140, "w"),
            ("channel", "Channel", 80, "center"),
            ("question", "Question", 320, "w"),
            ("created", "Created", 160, "center"),
            ("status", "Status", 80, "center"),
        ]:
            self.help_tree.heading(col, text=heading)
            self.help_tree.column(col, width=width, anchor=anchor)
        self.help_tree.pack(fill="both", expand=True, padx=5, pady=5)

        gradebook_frame = ttk.LabelFrame(inner, text="Recent Gradebook Preview")
        gradebook_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.gradebook_tree = ttk.Treeview(
            gradebook_frame,
            columns=("student", "quiz", "score", "correct", "time"),
            show="headings",
            height=6,
        )
        for col, heading, width in [
            ("student", "Student", 140),
            ("quiz", "Quiz", 180),
            ("score", "Score", 70),
            ("correct", "Correct", 80),
            ("time", "Time (s)", 80),
        ]:
            self.gradebook_tree.heading(col, text=heading)
            self.gradebook_tree.column(col, width=width, anchor="center")
        self.gradebook_tree.pack(fill="both", expand=True, padx=5, pady=5)

        charts_frame = ttk.Frame(inner)
        charts_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Row 1 charts
        perf_frame = ttk.LabelFrame(charts_frame, text="Student Performance")
        perf_frame.grid(row=0, column=0, padx=6, pady=6, sticky="nsew")
        self.performance_canvas = tk.Canvas(perf_frame, width=640, height=320, bg="white", highlightthickness=0)
        self.performance_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        self.performance_canvas.bind(
            "<Button-1>",
            lambda _: self._open_chart_popup("Student Performance", self._draw_performance_chart),
        )

        activity_frame = ttk.LabelFrame(charts_frame, text="Weekly Activity")
        activity_frame.grid(row=0, column=1, padx=6, pady=6, sticky="nsew")
        self.activity_canvas = tk.Canvas(activity_frame, width=640, height=320, bg="white", highlightthickness=0)
        self.activity_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        self.activity_canvas.bind(
            "<Button-1>",
            lambda _: self._open_chart_popup("Weekly Activity", self._draw_activity_chart),
        )

        # Row 2 charts
        difficulty_frame = ttk.LabelFrame(charts_frame, text="Questions by Difficulty")
        difficulty_frame.grid(row=1, column=0, padx=6, pady=6, sticky="nsew")
        self.difficulty_canvas = tk.Canvas(difficulty_frame, width=640, height=320, bg="white", highlightthickness=0)
        self.difficulty_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        self.difficulty_canvas.bind(
            "<Button-1>",
            lambda _: self._open_chart_popup("Questions by Difficulty", self._draw_difficulty_chart),
        )

        subject_frame = ttk.LabelFrame(charts_frame, text="Subject Performance")
        subject_frame.grid(row=1, column=1, padx=6, pady=6, sticky="nsew")
        self.subject_canvas = tk.Canvas(subject_frame, width=640, height=320, bg="white", highlightthickness=0)
        self.subject_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        self.subject_canvas.bind(
            "<Button-1>",
            lambda _: self._open_chart_popup("Subject Performance", self._draw_subject_chart),
        )

        charts_frame.columnconfigure(0, weight=1)
        charts_frame.columnconfigure(1, weight=1)
        charts_frame.rowconfigure(0, weight=1)
        charts_frame.rowconfigure(1, weight=1)

        return frame

    def _open_chart_popup(self, title: str, draw_fn) -> None:
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("900x600")
        canvas = tk.Canvas(popup, width=840, height=520, bg="white", highlightthickness=0)
        canvas.pack(fill="both", expand=True, padx=10, pady=10)
        canvas.update_idletasks()
        draw_fn(canvas)

    def _show_view(self, role: UserRole) -> None:
        for frame in [self.student_frame, self.teacher_frame]:
            frame.pack_forget()
        if role == UserRole.STUDENT:
            self.student_frame.pack(fill="both", expand=True)
        else:
            self.teacher_frame.pack(fill="both", expand=True)

    def refresh_view(self) -> None:
        self._hide_landing()
        user = self._get_selected_user()
        if not user:
            return
        self._show_view(user.role)
        self.help_button.state(["!disabled"] if user.role == UserRole.STUDENT else ["disabled"])
        if user.role == UserRole.STUDENT:
            self._populate_quizzes()
            self.refresh_student_dashboard(user.user_id)
        else:
            self.refresh_teacher_dashboard(user.user_id)

    def _get_selected_user(self):
        user_id = self.selected_user.get()
        return self.system.users.get(user_id)

    def _on_student_click(self, event=None):
        selection = self.roster_tree.focus()
        if not selection:
            return
        user_id = selection
        self._show_student_popup(user_id)

    def _show_student_popup(self, user_id: str) -> None:
        try:
            profile = self.system.student_profile(user_id)
        except Exception as exc:  # pragma: no cover - UI only
            messagebox.showerror("TwoTor", f"Unable to load student: {exc}")
            return
        popup = tk.Toplevel(self.root)
        popup.title(f"Student Snapshot - {profile['user']['name']}")
        popup.geometry("620x640")

        ttk.Label(popup, text=profile["user"]["name"], font=("Segoe UI", 14, "bold")).pack(pady=6)
        ttk.Label(
            popup,
            text=f"Predicted next score: {profile.get('predicted_next_score') or 'n/a'}%",
            font=("Segoe UI", 10),
        ).pack()

        mastery_frame = ttk.LabelFrame(popup, text="Mastery")
        mastery_frame.pack(fill="x", padx=10, pady=8)
        for skill, value in profile["mastery"].items():
            ttk.Label(mastery_frame, text=f"{skill.title()}: {value:.2f}").pack(anchor="w", padx=6)

        attempts_frame = ttk.LabelFrame(popup, text="Assessments")
        attempts_frame.pack(fill="both", expand=True, padx=10, pady=8)
        ttk.Label(
            attempts_frame,
            text=(
                f"Attempts: {profile['attempt_stats']['total_attempts']} | "
                f"Avg: {profile['attempt_stats']['average_score'] or 'n/a'} | "
                f"Latest: {profile['attempt_stats']['latest_quiz'] or 'n/a'}"
            ),
        ).pack(anchor="w", padx=6, pady=4)
        text = tk.Text(attempts_frame, height=8, wrap="word", state="disabled")
        text.pack(fill="both", expand=True, padx=5, pady=5)
        recent_lines = "\n".join(
            f"{a['quiz_id']}: {a['score']}% ({a['correct_count']}/{a['total_questions']})"
            for a in profile["attempts"]
        ) or "No attempts yet."
        self._update_text_widget(text, recent_lines)

        lesson_frame = ttk.LabelFrame(popup, text="Lesson Progress")
        lesson_frame.pack(fill="both", expand=True, padx=10, pady=8)
        lesson_meta = profile["lesson_progress"]
        ttk.Label(
            lesson_frame,
            text=(
                f"Completed: {lesson_meta['completed_count']} | "
                f"Minutes: {lesson_meta['total_minutes']}"
            ),
        ).pack(anchor="w", padx=6, pady=4)
        lesson_text = tk.Text(lesson_frame, height=6, wrap="word", state="disabled")
        lesson_text.pack(fill="both", expand=True, padx=5, pady=5)
        lesson_lines = "\n".join(
            f"{entry['lesson_id']} - {entry['minutes_spent']} min @ {entry['completed_at']}"
            for entry in lesson_meta["recent"]
        ) or "No lessons completed yet."
        self._update_text_widget(lesson_text, lesson_lines)

        help_frame = ttk.LabelFrame(popup, text="Help Requests")
        help_frame.pack(fill="both", expand=True, padx=10, pady=8)
        help_text = tk.Text(help_frame, height=6, wrap="word", state="disabled")
        help_text.pack(fill="both", expand=True, padx=5, pady=5)
        help_lines = "\n".join(
            f"{item['created_at']}: {item['question']} [{item['status']}]"
            for item in profile["help_requests"]
        ) or "No help requests logged."
        self._update_text_widget(help_text, help_lines)

    def _populate_quizzes(self) -> None:
        self.quiz_list.delete(0, tk.END)
        for quiz in self.quiz_map.values():
            label = f"{quiz.title} ({'Graded' if quiz.graded else 'Practice'})"
            self.quiz_list.insert(tk.END, f"{quiz.quiz_id} :: {label}")

    def _populate_lessons(self, lessons: list[dict]) -> None:
        self.lesson_list.delete(0, tk.END)
        if not lessons:
            self.lesson_list.insert(tk.END, "No lessons available.")
            return
        for lesson in lessons:
            status = "✓" if lesson.get("completed") else "•"
            self.lesson_list.insert(
                tk.END,
                f"{status} {lesson['title']} ({lesson['skill'].title()}) - {lesson['estimated_minutes']} min",
            )

    def refresh_student_dashboard(self, user_id: str) -> None:
        payload = self.system.student_dashboard(user_id)

        self.mastery_list.delete(0, tk.END)
        for skill, value in payload["mastery"].items():
            self.mastery_list.insert(tk.END, f"{skill.title()}: {value:.2f}")

        prediction = payload.get("predicted_next_score")
        self.prediction_var.set(
            "Predicted next score: n/a" if prediction is None else f"Predicted next score: {prediction:.1f}%"
        )

        attempts = payload.get("recent_attempts", [])
        self._update_text_widget(
            self.attempts_text,
            "\n".join(
                f"{item['quiz_id']}: {item['score']}% ({item['correct_count']}/{item['total_questions']})"
                for item in attempts
            )
            or "No attempts yet. Launch a practice quiz to begin.",
        )
        self.lesson_payload = payload.get("lessons", [])
        self._populate_lessons(self.lesson_payload)

    def refresh_teacher_dashboard(self, user_id: str) -> None:
        payload = self.system.teacher_dashboard(user_id)
        self.teacher_payload = payload

        self.attempt_velocity_var.set(f"Attempt velocity (per quiz): {payload.get('attempt_velocity', 0)}")

        for item in self.roster_tree.get_children():
            self.roster_tree.delete(item)
        for student in payload.get("class_roster", []):
            self.roster_tree.insert(
                "",
                "end",
                iid=student["user_id"],
                values=(
                    student["name"],
                    student["average_score"] if student["average_score"] is not None else "n/a",
                    student["predicted_score"] if student["predicted_score"] is not None else "n/a",
                    student["attempts"],
                    student["last_quiz"] or "n/a",
                ),
            )

        self.at_risk_list.delete(0, tk.END)
        for student in payload.get("at_risk_students", []):
            self.at_risk_list.insert(
                tk.END,
                f"{student['name']} ({student['predicted_score']}%)",
            )
        if not payload.get("at_risk_students"):
            self.at_risk_list.insert(tk.END, "No students below 50% projection.")

        for item in self.help_tree.get_children():
            self.help_tree.delete(item)
        for ticket in payload.get("help_requests", []):
            self.help_tree.insert(
                "",
                "end",
                values=(
                    ticket["student"],
                    ticket["channel"],
                    ticket["question"][:60] + ("..." if len(ticket["question"]) > 60 else ""),
                    ticket["created_at"].split("T")[0],
                    ticket["status"].title(),
                ),
            )
        if not payload.get("help_requests"):
            self.help_tree.insert("", "end", values=("No help requests yet", "", "", "", ""))

        for item in self.gradebook_tree.get_children():
            self.gradebook_tree.delete(item)
        for row in payload.get("gradebook_preview", []):
            self.gradebook_tree.insert(
                "",
                "end",
                values=(
                    row["student"],
                    row["quiz"],
                    row["score"],
                    row["correct"],
                    row["time_seconds"],
                ),
            )

        # Save payload for chart data
        self.student_mastery_scores = payload.get("student_mastery_scores", [])
        self._draw_performance_chart()
        self._draw_activity_chart()
        self._draw_difficulty_chart()
        self._draw_subject_chart(mastery_scores=self.student_mastery_scores)

    def start_quiz(self) -> None:
        user = self._get_selected_user()
        if not user or user.role != UserRole.STUDENT:
            messagebox.showinfo("TwoTor", "Choose a student account to launch a quiz.")
            return
        selection = self.quiz_list.curselection()
        if not selection:
            messagebox.showinfo("TwoTor", "Select a quiz to begin.")
            return
        quiz_id = self.quiz_list.get(selection[0]).split(" :: ")[0]
        quiz = self.quiz_map.get(quiz_id)
        if not quiz:
            messagebox.showerror("TwoTor", f"Quiz {quiz_id} not found.")
            return
        QuizWindow(self.root, quiz, lambda answers: self._complete_quiz(quiz_id, answers))

    def _complete_quiz(self, quiz_id: str, answers: list[int]) -> None:
        user = self._get_selected_user()
        if not user:
            return
        time_spent = max(180, len(answers) * 90)
        result = self.system.take_quiz(user.user_id, quiz_id, answers, time_spent)
        feedback_lines = "\n".join(result["feedback"])
        skill_updates = "\n".join(
            f"{skill.title()}: {value:.3f}" for skill, value in result["skill_updates"].items()
        )

        summary = (
            f"Attempt Summary:\n"
            f"- Score: {result['attempt']['score']}%\n"
            f"- Correct: {result['attempt']['correct_count']} / {result['attempt']['total_questions']}\n"
            f"- Updated Skills:\n{skill_updates or 'n/a'}\n"
        )
        self._update_text_widget(
            self.feedback_text,
            f"{summary}\nDetailed Feedback:\n{feedback_lines}",
        )
        self.refresh_view()
        messagebox.showinfo(
            "TwoTor",
            f"Quiz submitted! Predicted next score: {result.get('prediction', 'n/a')}%",
        )

    def mark_lesson_read(self) -> None:
        user = self._get_selected_user()
        if not user or user.role != UserRole.STUDENT:
            messagebox.showinfo("TwoTor", "Choose a student account to record a lesson.")
            return
        if not self.lesson_payload:
            messagebox.showinfo("TwoTor", "No lessons available to mark complete.")
            return
        selection = self.lesson_list.curselection()
        if not selection:
            messagebox.showinfo("TwoTor", "Select a lesson to mark as read.")
            return
        lesson = self.lesson_payload[selection[0]]
        try:
            result = self.system.record_lesson_participation(
                user.user_id, lesson["lesson_id"], lesson.get("estimated_minutes", 10)
            )
        except Exception as exc:  # pragma: no cover - UI only
            messagebox.showerror("TwoTor", f"Unable to record lesson: {exc}")
            return
        self.refresh_view()
        messagebox.showinfo(
            "TwoTor",
            f"Marked '{lesson['title']}' as read.\nUpdated mastery: {result['mastery']}",
        )

    def request_help(self) -> None:
        user = self._get_selected_user()
        if not user or user.role != UserRole.STUDENT:
            messagebox.showinfo("TwoTor", "Help requests are available for students.")
            return
        question = simpledialog.askstring(
            "TwoTor Help",
            "Describe where you're stuck (e.g., limits, functions, trig identities):",
        )
        if not question:
            return
        channel = "assignment"
        ticket = self.system.request_help(user.user_id, channel, question)
        messagebox.showinfo(
            "TwoTor Help",
            f"Ticket {ticket['ticket_id']} responded:\n{ticket['response']}",
        )

    def _update_text_widget(self, widget: tk.Text, content: str) -> None:
        widget.config(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert(tk.END, content)
        widget.config(state="disabled")

    # region landing helpers
    def _show_landing(self):
        self.top_frame.pack_forget()
        self.student_frame.pack_forget()
        self.teacher_frame.pack_forget()
        self.landing_frame.pack(fill="both", expand=True)

    def _hide_landing(self):
        if self.landing_frame.winfo_manager():
            self.landing_frame.pack_forget()
            self.top_frame.pack(fill="x", padx=10, pady=10)

    def _choose_student(self):
        if self.students:
            self.selected_user.set(self.students[0].user_id)
        self.refresh_view()

    def _choose_teacher(self):
        if self.teachers:
            self.selected_user.set(self.teachers[0].user_id)
        self.refresh_view()

    # endregion

    # region chart drawers
    def _draw_performance_chart(self, canvas: tk.Canvas | None = None):
        canvas = canvas or self.performance_canvas
        canvas.delete("all")
        data = [("Emma", 82), ("Liam", 89), ("Sophia", 67), ("Noah", 93), ("Ava", 75), ("Ethan", 58)]
        w = int(canvas.winfo_width() or 480)
        h = int(canvas.winfo_height() or 260)
        margin = 40
        bar_width = (w - 2 * margin) / len(data) * 0.6
        max_val = max(val for _, val in data)
        for idx, (name, val) in enumerate(data):
            x_center = margin + idx * ((w - 2 * margin) / len(data)) + ((w - 2 * margin) / len(data)) / 2
            bar_height = (h - 2 * margin) * (val / max_val)
            canvas.create_rectangle(
                x_center - bar_width / 2,
                h - margin - bar_height,
                x_center + bar_width / 2,
                h - margin,
                fill="#8c6cf5",
                width=0,
            )
            canvas.create_text(x_center, h - margin + 12, text=name, font=("Segoe UI", 9))

    def _draw_activity_chart(self, canvas: tk.Canvas | None = None):
        canvas = canvas or self.activity_canvas
        canvas.delete("all")
        days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
        lessons = [12, 15, 10, 18, 14]
        quizzes = [18, 21, 16, 24, 20]
        w = int(canvas.winfo_width() or 480)
        h = int(canvas.winfo_height() or 260)
        margin = 40
        y_max = max(lessons + quizzes)

        def plot_line(values, color):
            points = []
            for idx, val in enumerate(values):
                x = margin + idx * ((w - 2 * margin) / (len(values) - 1))
                y = h - margin - (h - 2 * margin) * (val / y_max)
                points.append((x, y))
            for i in range(len(points) - 1):
                canvas.create_line(points[i][0], points[i][1], points[i + 1][0], points[i + 1][1], fill=color, width=2)
            for x, y in points:
                canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill=color, outline=color)
            return points

        plot_line(lessons, "#a86cf7")
        plot_line(quizzes, "#1aa9d8")

        for idx, day in enumerate(days):
            x = margin + idx * ((w - 2 * margin) / (len(days) - 1))
            canvas.create_text(x, h - margin + 12, text=day, font=("Segoe UI", 9))

    def _draw_difficulty_chart(self, canvas: tk.Canvas | None = None):
        canvas = canvas or self.difficulty_canvas
        canvas.delete("all")
        slices = [("Easy", 45, "#1cad6f"), ("Medium", 35, "#f9a825"), ("Hard", 20, "#e53935")]
        w = int(canvas.winfo_width() or 480)
        h = int(canvas.winfo_height() or 260)
        radius = min(w, h) * 0.28
        center = (w / 2, h / 2 + 10)
        start = 0
        for label, pct, color in slices:
            extent = pct / 100 * 360
            canvas.create_arc(
                center[0] - radius,
                center[1] - radius,
                center[0] + radius,
                center[1] + radius,
                start=start,
                extent=extent,
                fill=color,
                outline="white",
                width=2,
                style="pieslice",
            )
            mid_angle = (start + extent / 2) * pi / 180
            lx = center[0] + (radius + 40) * cos(mid_angle)
            ly = center[1] + (radius + 40) * sin(mid_angle)
            canvas.create_line(
                center[0] + radius * cos(mid_angle),
                center[1] + radius * sin(mid_angle),
                lx,
                ly,
                fill=color,
                width=2,
            )
            canvas.create_text(lx, ly, text=f"{label}: {pct}%", font=("Segoe UI", 9, "bold"), fill=color, anchor="c")
            start += extent

    def _draw_subject_chart(self, canvas: tk.Canvas | None = None, mastery_scores: list[dict] | None = None):
        canvas = canvas or self.subject_canvas
        canvas.delete("all")
        mastery_scores = mastery_scores if mastery_scores is not None else self.student_mastery_scores
        if not mastery_scores:
            canvas.create_text(
                (canvas.winfo_width() or 400) / 2,
                (canvas.winfo_height() or 240) / 2,
                text="No mastery data available.",
                font=("Segoe UI", 10, "bold"),
            )
            return
        w = int(canvas.winfo_width() or 480)
        h = int(canvas.winfo_height() or 260)
        margin = 30
        label_width = 180
        bar_height = 20
        usable_width = max(w - 2 * margin - label_width, 120)
        max_score = max(entry.get("mastery_score", 0) for entry in mastery_scores) or 1
        for idx, entry in enumerate(mastery_scores):
            pct = entry.get("mastery_score", 0)
            y = margin + idx * (bar_height + 12)
            if y + bar_height > h - margin:
                break
            canvas.create_text(
                margin,
                y + bar_height / 2,
                text=entry.get("name", "Student"),
                anchor="w",
                font=("Segoe UI", 10, "bold"),
            )
            canvas.create_rectangle(
                margin + label_width,
                y,
                margin + label_width + usable_width,
                y + bar_height,
                fill="#e6e9f0",
                outline="",
            )
            fill_width = usable_width * (pct / max_score)
            canvas.create_rectangle(
                margin + label_width,
                y,
                margin + label_width + fill_width,
                y + bar_height,
                fill="#0a0a1a",
                outline="",
            )
            canvas.create_text(
                margin + label_width + usable_width + 8,
                y + bar_height / 2,
                text=f"{pct:.1f}%",
                anchor="w",
                font=("Segoe UI", 10, "bold"),
            )

    # endregion


def launch_gui(data_dir: Path) -> None:
    system = TutoringSystem(data_dir)
    root = tk.Tk()
    TwoTorGUI(root, system)
    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch the TwoTor GUI.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).parent / "data",
        help="Directory containing sample_content.json and state.json",
    )
    args = parser.parse_args()
    launch_gui(args.data_dir)


if __name__ == "__main__":
    main()
