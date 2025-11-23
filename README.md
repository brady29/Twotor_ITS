TwoTor Intelligent Tutoring System
==================================

This repository contains a fully functioning Python-based intelligent tutoring system (ITS) that follows the CIS 3750 post-mortem guidance for Group TwoTor. The system keeps the demo's five use cases front-and-center (teaching, testing, grading, login/user creation, and reporting/analytics) while adding the long-term fixes that the TA and participants requested—consistent navigation, profile/settings touchpoints, redirection between related screens, comprehensive quiz feedback, and stronger error handling.

Key features
------------
- **Adaptive practice & testing** – Distinguishes practice vs graded quizzes, enforces time limits, and shows every answer choice in the feedback bundle so students can learn from mistakes.
- **Pre-trained intelligence** – Wraps a Bayesian Knowledge Tracing model (`twotor_its.bkt`) and a fixed-weight linear regression model (`twotor_its.regression`) to personalize skill mastery and predict the next score.
- **Role-specific dashboards** – Students see mastery snapshots, BKT-driven predictions, and consistent nav links; teachers inspect course rosters, attempt velocity, and can export gradebooks (CSV/Excel-ready) for compliance with the “percent over letter grade” request.
- **Reporting & exports** – `python main.py export-grades --dest exports/gradebook.csv` produces analytics-friendly tables, aligning with the grading/reporting use cases.
- **Help flows** – `python main.py help ...` routes to either appointment scheduling or immediate chatbot nudges per the “clarify help” recommendation.
- **Username safety checks** – `python main.py validate-username <name>` blocks vulgar usernames and explains why, covering the login edge-case flagged by Jeremy.

Project structure
-----------------
```
.
├── data/
│   ├── sample_content.json   # Seed users, courses, modules, and quizzes
│   └── state.json            # Attempts + BKT mastery, grows as you use the app
├── exports/                  # Created on demand for gradebook CSVs
├── twotor_its/
│   ├── analytics.py          # Gradebook rows, mastery snapshots, quiz feedback
│   ├── bkt.py                # Bayesian Knowledge Tracing implementation
│   ├── helpdesk.py           # Appointment vs assignment help routing
│   ├── models.py             # Dataclasses for users, courses, quizzes, attempts
│   ├── policy.py             # Username restriction checks
│   ├── regression.py         # Fixed-weight linear regression forecaster
│   ├── storage.py            # JSON persistence layer
│   └── tutoring.py           # Orchestrates the tutoring logic + dashboards
└── main.py                   # CLI entry point with consistent nav commands
```

Running the CLI
---------------
All commands assume you are inside the repository root.

### GUI (recommended for learners)
Launch the guided, pre-calculus focused GUI:
```bash
python gui.py
```
You can pick a student account (e.g., `stu-cole`), review mastery, launch either the practice warmup or graded analytics checkpoint, request help, and see detailed feedback without leaving the window. The GUI persists attempts/state just like the CLI.

1. **Display the global navigation (consistency check):**
   ```bash
   python main.py nav
   ```
2. **List quizzes (practice + graded):**
   ```bash
   python main.py list-quizzes
   python main.py list-quizzes --graded-only
   ```
3. **Take a quiz as a student** (answers are 1-based to match on-screen ordering):
   ```bash
   python main.py take-quiz \
       --user stu-cole \
       --quiz quiz-practice-01 \
       --answers 3 2 3 \
       --time-seconds 420
   ```
   The response includes:
   - Attempt summary (score, correctness, time)
   - Per-skill BKT updates
   - Regression-based score forecast
   - Feedback lines that repeat *all* choices (per testing use-case feedback)
4. **Check dashboards:**
   ```bash
   python main.py dashboard --user stu-cole
   python main.py dashboard --user teach-ramy
   ```
5. **Export grades to CSV (analytics/grading use case):**
   ```bash
   python main.py export-grades --dest exports/gradebook.csv
   ```
6. **Route help requests (appointment vs assignment help paths):**
   ```bash
   python main.py help \
       --user stu-cole \
       --channel assignment \
       --question "Need clarification on slip probability"
   ```
7. **Validate usernames (login/user creation improvements):**
   ```bash
   python main.py validate-username clean_student
   python main.py validate-username vile_user123   # rejected with explanation
   ```

Extending the system
--------------------
- **Content** – Update `data/sample_content.json` with additional courses, modules, or quizzes. Skills should match the BKT parameter keys (`algebra`, `calculus`, `statistics`, `foundations`) unless you also extend `twotor_its.bkt.default_bkt_model`.
- **State** – `data/state.json` is generated automatically when missing. You can reset progress by deleting the file (if you want a pristine run).
- **Regression weights** – Swap out or retrain `default_regression_model()` inside `twotor_its/regression.py` if you have institution-specific historical data.
- **Username rules** – Modify `twotor_its/policy.py` to expand the banned-word list or add regex checks for institution policy alignment.

Testing performed
-----------------
- `python main.py nav` – confirms consistent navigation payload.
- `python main.py list-quizzes` – verifies quiz catalog loading.
- `python main.py dashboard --user stu-cole` – validatdent view and empty state.
- `python main.py take-quiz ...` – exercises BKT updates, rees stugression prediction, and detailed feedback.
- `python main.py dashboard --user teach-ramy` – validates teacher analytics payload.
- `python main.py export-grades --dest exports/gradebook.csv` – confirms CSV export pipeline.
- `python main.py help ...` – checks appointment vs assignment routing.
- `python main.py validate-username ...` – ensures restricted username detection works.
