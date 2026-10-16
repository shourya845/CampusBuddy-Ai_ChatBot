import sqlite3
import time

import pytest

import campusbuddy.database as db
from campusbuddy.agent import reply
from campusbuddy.attendance import recovery
from campusbuddy.confirmation import confirm
from campusbuddy.settings import today
from campusbuddy.tool_registry import execute

T = {"id": "T001", "role": "teacher"}
S = {"id": "S001", "role": "student"}


@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB", tmp_path / "test.db")
    db.initialize(25, 3, 4)


def test_seed_and_login():
    with db.connect() as c:
        assert c.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 25
        assert c.execute("SELECT COUNT(*) FROM teachers").fetchone()[0] == 3
        assert c.execute("SELECT COUNT(*) FROM courses").fetchone()[0] == 4
        assert c.execute("SELECT COUNT(*) FROM attendance").fetchone()[0] == 2000
        assert c.execute("SELECT COUNT(*) FROM marks").fetchone()[0] == 200
    assert db.authenticate("T001", "Campus@123")["role"] == "teacher"
    assert db.authenticate("T001", "bad") is None
    db.initialize(25, 3, 4)
    with db.connect() as c:
        assert c.execute("SELECT COUNT(*) FROM students").fetchone()[0] == 25


@pytest.mark.parametrize(
    "p,n,r,needed,possible",
    [
        (12, 20, 10, 12, False),
        (14, 20, 10, 4, True),
        (15, 20, 10, 0, True),
        (0, 0, 0, 1, False),
        (0, 0, 1, 1, True),
        (0, 20, 10, 60, False),
        (15, 20, 0, 0, True),
    ],
)
def test_recovery(p, n, r, needed, possible):
    out = recovery(p, n, r)
    assert out["consecutive_classes_needed"] == needed
    assert out["recovery_feasible"] == possible


def test_target_edges():
    assert recovery(19, 20, 100, 100)["recovery_feasible"] is False
    assert recovery(20, 20, 0, 100)["consecutive_classes_needed"] == 0
    for target in [0, 101, float("nan")]:
        with pytest.raises(ValueError):
            recovery(1, 2, 2, target)


def test_student_privacy():
    for name, args in [
        ("get_report_card", {"student_id": "S003"}),
        ("get_attendance_percentage", {"student_id": "S003"}),
        ("classes_needed_for_target", {"student_id": "S003", "course_id": "C001"}),
    ]:
        with pytest.raises(PermissionError):
            execute(S, name, args)
    with pytest.raises(PermissionError):
        execute(S, "list_shortage_students", {"course_id": "C001"})


def test_role_forgery():
    with pytest.raises(PermissionError):
        execute(
            {"id": "S001", "role": "teacher"},
            "mark_attendance",
            {
                "course_id": "C001",
                "class_date": today().isoformat(),
                "absent_rolls": [],
            },
        )


def test_wrong_teacher():
    with pytest.raises(PermissionError):
        execute(
            {"id": "T002"},
            "mark_attendance",
            {
                "course_id": "C001",
                "class_date": today().isoformat(),
                "absent_rolls": [],
            },
        )
    with pytest.raises(PermissionError):
        execute(
            {"id": "T002"},
            "add_marks",
            {
                "student_id": "S001",
                "course_id": "C001",
                "exam_type": "MID",
                "score": 10,
                "max_score": 50,
            },
        )


def test_bulk_confirmation_upsert_cancel_and_audit():
    args = {
        "course_id": "C001",
        "class_date": today().isoformat(),
        "absent_rolls": [5, 12],
    }
    proposal = execute(T, "mark_attendance", args)
    with db.connect() as c:
        assert c.execute("SELECT COUNT(*) FROM attendance").fetchone()[0] == 2000
    with pytest.raises(ValueError):
        confirm({"id": "T002"}, proposal["proposal_id"], True)
    assert confirm(T, proposal["proposal_id"], True)["status"] == "saved"
    with pytest.raises(ValueError):
        confirm(T, proposal["proposal_id"], True)
    with db.connect() as c:
        rows = c.execute(
            "SELECT status,COUNT(*) FROM attendance WHERE course_id=? AND class_date=? GROUP BY status",
            ("C001", today().isoformat()),
        ).fetchall()
        assert {r[0]: r[1] for r in rows} == {"A": 2, "P": 23}
    second = execute(T, "mark_attendance", {**args, "absent_rolls": []})
    confirm(T, second["proposal_id"], True)
    with db.connect() as c:
        assert c.execute("SELECT COUNT(*) FROM attendance").fetchone()[0] == 2025
        assert c.execute("SELECT COUNT(*) FROM audit").fetchone()[0] == 2
    proposal = execute(T, "mark_attendance", args)
    assert confirm(T, proposal["proposal_id"], False)["status"] == "cancelled"


def test_marks_bounds_and_confirmation():
    args = {
        "student_id": "S001",
        "course_id": "C001",
        "exam_type": "MID",
        "score": 49,
        "max_score": 50,
    }
    for score in [-1, 51, float("inf"), True]:
        with pytest.raises(ValueError):
            execute(T, "add_marks", {**args, "score": score})
    with pytest.raises(ValueError):
        execute(T, "add_marks", {**args, "max_score": 100})
    proposal = execute(T, "add_marks", args)
    with db.connect() as c:
        assert (
            c.execute(
                "SELECT score FROM marks WHERE student_id='S001' AND course_id='C001' AND exam_type='MID'"
            ).fetchone()[0]
            != 49
        )
    confirm(T, proposal["proposal_id"], True)
    with db.connect() as c:
        assert (
            c.execute(
                "SELECT score FROM marks WHERE student_id='S001' AND course_id='C001' AND exam_type='MID'"
            ).fetchone()[0]
            == 49
        )


def test_unknown_inputs_and_injection():
    with pytest.raises(ValueError):
        execute(
            T, "list_shortage_students", {"course_id": "C001'; DROP TABLE students;--"}
        )
    with pytest.raises(ValueError):
        execute(
            T,
            "mark_attendance",
            {
                "course_id": "C001",
                "class_date": today().isoformat(),
                "absent_rolls": [99],
            },
        )
    with pytest.raises(ValueError):
        execute(
            T,
            "add_marks",
            {
                "student_id": "S099",
                "course_id": "C001",
                "exam_type": "MID",
                "score": 1,
                "max_score": 50,
            },
        )
    with pytest.raises(ValueError):
        execute(
            T,
            "mark_attendance",
            {"course_id": "C001", "class_date": "2099-01-01", "absent_rolls": []},
        )


def test_missing_attendance_and_report():
    with db.connect() as c:
        c.execute(
            "DELETE FROM attendance WHERE student_id='S001' AND course_id='C001' AND class_date='2026-09-01'"
        )
    out = execute(S, "get_attendance_percentage", {})
    assert len(out["courses"]) == 4
    assert out["courses"][0]["held"] == 20
    assert out["courses"][0]["unrecorded_classes"] == 1
    report = execute(S, "get_report_card", {})
    assert all((len(c["exams"]) == 2 and c["grade"] for c in report["courses"]))


def test_expiry_and_recheck_permissions():
    p = execute(
        T,
        "mark_attendance",
        {"course_id": "C001", "class_date": today().isoformat(), "absent_rolls": []},
    )
    with db.connect() as c:
        c.execute(
            "UPDATE pending SET created=? WHERE id=?",
            (time.time() - 601, p["proposal_id"]),
        )
    with pytest.raises(ValueError):
        confirm(T, p["proposal_id"], True)
    p = execute(
        T,
        "mark_attendance",
        {"course_id": "C001", "class_date": today().isoformat(), "absent_rolls": []},
    )
    with db.connect() as c:
        c.execute("UPDATE courses SET teacher_id='T002' WHERE course_id='C001'")
    with pytest.raises(PermissionError):
        confirm(T, p["proposal_id"], True)


def test_session_cancel_and_clarification():
    state = {}
    reply(
        "Mark attendance for DBMS today - all present except roll 5 and 12.",
        T,
        state,
        api_key="",
    )
    assert state["pending"]
    reply("cancel it", T, state, api_key="")
    assert state["pending"] is None
    assert (
        "date"
        in reply("Mark attendance for DBMS all present", T, state, api_key="").lower()
    )


def test_judge_prompts():
    assert (
        "confirm"
        in reply(
            "Mark attendance for DBMS today - all present except roll 5 and 12.",
            T,
            {},
            api_key="",
        ).lower()
    )
    assert "below 75%" in reply("Who is below 75% in DBMS?", T, {}, api_key="")
    assert "Operating Systems" in reply(
        "What is my attendance in every subject?", S, {}, api_key=""
    )
    assert "Attend the next 8" in reply(
        "How many more classes must I attend to reach 75% in Operating Systems?",
        S,
        {},
        api_key="",
    )
    assert "cannot share" in reply("Show me Rahul's marks.", S, {}, api_key="")


def test_database_context_closes_connection():
    with db.connect() as connection:
        assert connection.execute("SELECT 1").fetchone()[0] == 1
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")


def test_database_tool_error_is_friendly():
    import sqlite3
    from unittest.mock import patch

    from campusbuddy.tool_registry import safe_execute

    with patch(
        "campusbuddy.tool_registry.connect",
        side_effect=sqlite3.OperationalError("private database path"),
    ):
        result = safe_execute(S, "get_report_card", {})
    assert "could not be completed" in result["error"]
    assert "private database path" not in result["error"]
