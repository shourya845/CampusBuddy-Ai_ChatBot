import hashlib
import hmac
import os
import sqlite3
from pathlib import Path

from .settings import ROOT, SCHEMA_PATH

DB = Path(os.getenv("CAMPUSBUDDY_DB", str(ROOT / "campusbuddy.db")))


class DatabaseConnection(sqlite3.Connection):
    def __exit__(self, *error_details):
        try:
            return super().__exit__(*error_details)
        finally:
            self.close()


def connect():
    connection = sqlite3.connect(DB, timeout=15, factory=DatabaseConnection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys=ON")
    return connection


def password(value, salt):
    return hashlib.pbkdf2_hmac(
        "sha256", value.encode(), bytes.fromhex(salt), 120000
    ).hex()


def authenticate(user_id, password_text):
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM users WHERE id=?", (user_id,)
        ).fetchone()
    if row and hmac.compare_digest(
        row["password_hash"], password(password_text, row["salt"])
    ):
        return {k: row[k] for k in ("id", "name", "role")}
    return None


def sample_counts():
    with connect() as connection:
        return {
            table: connection.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
            for table in (
                "users",
                "students",
                "teachers",
                "courses",
                "enrollments",
                "class_sessions",
                "attendance",
                "exams",
                "marks",
                "pending",
                "audit",
            )
        }


def initialize(student_count=200, teacher_count=25, course_count=5):
    with connect() as connection:
        connection.executescript(SCHEMA_PATH.read_text())
        populated = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if not populated:
        from database.seed import seed_sample_data

        seed_sample_data(student_count, teacher_count, course_count)
