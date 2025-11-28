TwoTor Intelligent Tutoring System


TwoTor is a Python intelligent tutoring system with both GUI and CLI entry points. Content lives in JSON (`data/sample_content.json`), state persists to `data/state.json`, and on startup the app auto-trains a lightweight linear regression to forecast the next quiz score (scikit-learn if installed, otherwise numpy OLS). Bayesian Knowledge Tracing (BKT) tracks per-skill mastery; predictions are clipped to 0–100 and shown on dashboards and after quiz submissions.

Key features
- **GUI-first flow:** `python gui.py` gives students quizzes, instant feedback, mastery snapshots, and help routing.
- **CLI parity:** Navigation, dashboards, quiz taking, help requests, and grade exports mirror the GUI.
- **Adaptive signals:** BKT mastery plus an auto-trained regression forecaster (`twotor_its.regression`) refreshed each launch from existing attempts.
- **Teacher tools:** Roster with average/predicted scores and at-risk flags, class mastery view, recent help tickets, and CSV export.
- **Safety:** Username validation rules in `twotor_its/policy.py`.

Quick start
Requirements: Python 3.11+. For best regression training install scikit-learn (`pip install scikit-learn`); without it the model falls back to numpy OLS or static defaults.

- Launch GUI (recommended):  
  `python gui.py`
- Show nav:  
  `python main.py nav`
- Student dashboard (example):  
  `python main.py dashboard --user stu-001`
- List quizzes:  
  `python main.py list-quizzes`  
  `python main.py list-quizzes --graded-only`
- Take a quiz (answers are 1-based):  
  `python main.py take-quiz --user stu-001 --quiz quiz-pre-01 --answers 1 2 3 --time-seconds 420`
- Request help:  
  `python main.py help --user stu-001 --channel appointment --question "Need review on limits"`
- Teacher dashboard:  
  `python main.py dashboard --user teach-ramy`
- Export gradebook:  
  `python main.py export-grades --dest exports/gradebook.csv`
- Validate usernames:  
  `python main.py validate-username clean_student`

Data and models
---------------
- `data/sample_content.json` seeds users, courses, modules, lessons, and quizzes (precalculus/calculus).
- `data/state.json` stores attempts, progress, help tickets, and lesson activity; created on first run and grows with use.
- Regression training at startup reuses historical attempts; feature recipe matches `_predict_next_score` (avg mastery, last score, time, attempts_last_week, question difficulty).
- BKT parameters live in `twotor_its/bkt.py`; mastery updates per question after each quiz submission.

Extending
---------
- Add or edit content in `data/sample_content.json`; align skill names with BKT parameters if you add new skills.
- Reset to a clean slate by deleting `data/state.json` (and any lesson activity files if present); they regenerate on next run.
