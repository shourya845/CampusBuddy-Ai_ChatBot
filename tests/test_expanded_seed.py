import campusbuddy.database as db
from campusbuddy.tool_registry import execute
from database.seed import seed_sample_data


def test_expand_preserves_existing_data_and_fills_related_tables(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB", tmp_path / "expanded.db")
    db.initialize(25, 3, 4)
    with db.connect() as c:
        original_hash = c.execute(
            "SELECT password_hash FROM users WHERE id='S001'"
        ).fetchone()[0]
        c.execute(
            "UPDATE marks SET score=42 WHERE student_id='S001' AND course_id='C001' AND exam_type='MID'"
        )
        c.execute(
            "UPDATE attendance SET status='A' WHERE student_id='S001' AND course_id='C001' AND class_date='2026-09-01'"
        )
    counts = seed_sample_data()
    assert counts == {
        "users": 225,
        "students": 200,
        "teachers": 25,
        "courses": 5,
        "enrollments": 1000,
        "class_sessions": 100,
        "attendance": 20000,
        "exams": 10,
        "marks": 2000,
        "pending": 0,
        "audit": 0,
    }
    assert seed_sample_data() == counts
    with db.connect() as c:
        assert c.execute("PRAGMA foreign_key_check").fetchall() == []
        assert c.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert (
            c.execute("SELECT password_hash FROM users WHERE id='S001'").fetchone()[0]
            == original_hash
        )
        assert (
            c.execute(
                "SELECT score FROM marks WHERE student_id='S001' AND course_id='C001' AND exam_type='MID'"
            ).fetchone()[0]
            == 42
        )
        assert (
            c.execute(
                "SELECT status FROM attendance WHERE student_id='S001' AND course_id='C001' AND class_date='2026-09-01'"
            ).fetchone()[0]
            == "A"
        )
    assert db.authenticate("S200", "Campus@123")["role"] == "student"
    assert db.authenticate("T025", "Campus@123")["role"] == "teacher"
    report = execute({"id": "S200"}, "get_report_card", {})
    assert len(report["courses"]) == 5
    assert all((len(course["exams"]) == 2 for course in report["courses"]))
    assert (
        execute({"id": "T004"}, "list_shortage_students", {"course_id": "C005"})[
            "course"
        ]
        == "Data Structures and Algorithms"
    )
