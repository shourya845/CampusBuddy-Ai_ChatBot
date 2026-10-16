from streamlit.testing.v1 import AppTest

import campusbuddy.database as db
from campusbuddy.settings import ROOT


def test_ui_login_student_and_logout(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB", tmp_path / "ui.db")
    db.initialize(25, 3, 4)
    monkeypatch.setenv("MODEL_PROVIDER", "demo")
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    assert not app.exception
    app.text_input[0].set_value("S001")
    app.text_input[1].set_value("Campus@123")
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state["actor"]["id"] == "S001"
    assert any((m.label == "Attendance" for m in app.metric))
    next(r for r in app.radio if r.label == "Navigation").set_value("Assistant").run()
    app.chat_input[0].set_value("What is my attendance in every subject?").run()
    assert not app.exception
    assert "Operating Systems" in app.session_state["chat"]["history"][-1]["content"]
    next((b for b in app.button if b.label == "Sign out")).click().run()
    assert not app.exception
    assert len(app.text_input) == 2


def test_ui_teacher_bulk_confirm(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB", tmp_path / "ui_teacher.db")
    db.initialize(25, 3, 4)
    monkeypatch.setenv("MODEL_PROVIDER", "demo")
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    app.text_input[0].set_value("T001")
    app.text_input[1].set_value("Campus@123")
    app.button[0].click().run()
    assert not app.exception
    next(r for r in app.radio if r.label == "Navigation").set_value("Assistant").run()
    app.chat_input[0].set_value(
        "Mark attendance for DBMS today - all present except roll 5 and 12."
    ).run()
    assert not app.exception
    assert app.session_state["chat"]["pending"]["present"] == 23
    next((b for b in app.button if b.label == "Confirm change")).click().run()
    assert not app.exception
    assert app.session_state["chat"]["pending"] is None
    with db.connect() as c:
        assert c.execute("SELECT COUNT(*) FROM audit").fetchone()[0] == 1


def test_login_database_error_is_friendly(tmp_path, monkeypatch):
    import sqlite3
    from unittest.mock import patch

    monkeypatch.setattr(db, "DB", tmp_path / "login_failure.db")
    db.initialize(25, 3, 4)
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    app.text_input[0].set_value("S001")
    app.text_input[1].set_value("Campus@123")
    with patch(
        "campusbuddy.ui.authenticate",
        side_effect=sqlite3.OperationalError("database locked"),
    ):
        app.button[0].click().run()
    assert not app.exception
    assert any(
        "Sign-in is temporarily unavailable" in error.value for error in app.error
    )


def test_course_database_error_is_friendly(tmp_path, monkeypatch):
    import sqlite3
    from unittest.mock import patch

    monkeypatch.setattr(db, "DB", tmp_path / "course_failure.db")
    db.initialize(25, 3, 4)
    monkeypatch.setenv("MODEL_PROVIDER", "demo")
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    app.text_input[0].set_value("S001")
    app.text_input[1].set_value("Campus@123")
    app.button[0].click().run()
    with patch(
        "campusbuddy.permissions.directory",
        side_effect=sqlite3.OperationalError("database locked"),
    ):
        app.run()
    assert not app.exception
    assert any(
        "course records are temporarily unavailable" in error.value
        for error in app.error
    )


def test_unassigned_teacher_dashboard(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB", tmp_path / "unassigned.db")
    db.initialize(200, 25, 5)
    monkeypatch.setenv("MODEL_PROVIDER", "demo")
    app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
    app.text_input[0].set_value("T025")
    app.text_input[1].set_value("Campus@123")
    app.button[0].click().run()
    assert not app.exception
    assert {m.label: m.value for m in app.metric}["My courses"] == "0"
    assert any("No courses are assigned" in item.value for item in app.info)
