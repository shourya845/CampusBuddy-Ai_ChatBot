import json
import os
import sqlite3
from datetime import date, datetime, timedelta

from campusbuddy.database import DB, connect, password, sample_counts
from campusbuddy.settings import SCHEMA_PATH

COURSE_SEEDS = [
    ("DBMS", "DBMS", "T001"),
    ("OS", "Operating Systems", "T001"),
    ("CN", "Computer Networks", "T002"),
    ("SE", "Software Engineering", "T003"),
    ("DSA", "Data Structures and Algorithms", "T004"),
]


def seed_sample_data(student_count=200, teacher_count=25, course_count=5):
    if not (
        25 <= student_count <= 999
        and 3 <= teacher_count <= 999
        and (4 <= course_count <= 5)
    ):
        raise ValueError(
            "Sample dataset requires 25-999 students, 3-999 teachers, and 4-5 courses."
        )
    if course_count == 5 and teacher_count < 4:
        raise ValueError("Five courses require at least four teachers.")
    names = [
        "Aarav",
        "Ananya",
        "Rahul",
        "Diya",
        "Arjun",
        "Ishita",
        "Rohan",
        "Meera",
        "Kabir",
        "Sara",
        "Vivaan",
        "Nisha",
        "Aditya",
        "Tara",
        "Dev",
        "Riya",
        "Aryan",
        "Pooja",
        "Kunal",
        "Neha",
        "Aman",
        "Sneha",
        "Yash",
        "Simran",
        "Varun",
    ]
    surnames = ["Sharma", "Verma", "Singh", "Gupta", "Patel", "Joshi", "Rao", "Mehta"]
    teacher_names = [
        "Dr. Sharma",
        "Dr. Verma",
        "Dr. Singh",
        "Dr. Nair",
        "Dr. Kapoor",
        "Dr. Bhatia",
        "Dr. Saxena",
        "Dr. Mishra",
        "Dr. Chauhan",
        "Dr. Sethi",
        "Dr. Pandey",
        "Dr. Agarwal",
        "Dr. Das",
        "Dr. Roy",
        "Dr. Iyer",
        "Dr. Menon",
        "Dr. Kulkarni",
        "Dr. Desai",
        "Dr. Chawla",
        "Dr. Arora",
        "Dr. Malhotra",
        "Dr. Tiwari",
        "Dr. Bansal",
        "Dr. Khanna",
        "Dr. Sinha",
    ]
    with connect() as connection:
        connection.executescript(SCHEMA_PATH.read_text())
        connection.execute("BEGIN IMMEDIATE")
        existing = {record[0] for record in connection.execute("SELECT id FROM users")}
        for role, n, prefix in [
            ("teacher", teacher_count, "T"),
            ("student", student_count, "S"),
        ]:
            for i in range(1, n + 1):
                user_id = f"{prefix}{i:03}"
                name = (
                    (
                        names[i - 1]
                        if i <= 25
                        else names[(i - 1) % 25]
                        + " "
                        + surnames[(i - 1) // 25 % len(surnames)]
                    )
                    if role == "student"
                    else teacher_names[(i - 1) % 25] + (f" {i}" if i > 25 else "")
                )
                if user_id not in existing:
                    salt = os.urandom(16).hex()
                    connection.execute(
                        "INSERT INTO users VALUES(?,?,?,?,?)",
                        (user_id, name, role, salt, password("Campus@123", salt)),
                    )
                profile = connection.execute(
                    "SELECT name,role FROM users WHERE id=?", (user_id,)
                ).fetchone()
                if profile["role"] != role:
                    raise ValueError(
                        "Existing sample ID has a conflicting role: " + user_id
                    )
                if role == "student":
                    connection.execute(
                        "INSERT OR IGNORE INTO students VALUES(?,?,?,?,?)",
                        (user_id, i, profile["name"], "Computer Science", 5),
                    )
                else:
                    connection.execute(
                        "INSERT OR IGNORE INTO teachers VALUES(?,?,?)",
                        (user_id, profile["name"], f"teacher{i}@campus.example"),
                    )
        for j, (code, name, teacher) in enumerate(COURSE_SEEDS[:course_count], 1):
            course_id = f"C{j:03}"
            connection.execute(
                "INSERT OR IGNORE INTO courses VALUES(?,?,?,?,?)",
                (course_id, code, name, teacher, 30),
            )
            dates = [
                (date(2026, 9, 1) + timedelta(days=k)).isoformat() for k in range(20)
            ]
            connection.executemany(
                "INSERT OR IGNORE INTO class_sessions VALUES(?,?)",
                [(course_id, d) for d in dates],
            )
            connection.executemany(
                "INSERT OR IGNORE INTO exams VALUES(?,?,?)",
                [(course_id, "MID", 50), (course_id, "FINAL", 100)],
            )
            sessions = [
                record[0]
                for record in connection.execute(
                    "SELECT class_date FROM class_sessions WHERE course_id=? ORDER BY class_date",
                    (course_id,),
                )
            ]
            exams = connection.execute(
                "SELECT exam_type,max_score FROM exams WHERE course_id=?", (course_id,)
            ).fetchall()
            for i in range(1, student_count + 1):
                student_id = f"S{i:03}"
                connection.execute(
                    "INSERT OR IGNORE INTO enrollments VALUES(?,?)",
                    (student_id, course_id),
                )
                attended = 10 + (i + j) % 11
                connection.executemany(
                    "INSERT OR IGNORE INTO attendance VALUES(?,?,?,?)",
                    [
                        (student_id, course_id, d, "P" if k % 20 < attended else "A")
                        for (k, d) in enumerate(sessions)
                    ],
                )
                for exam in exams:
                    maximum = exam["max_score"]
                    connection.execute(
                        "INSERT OR IGNORE INTO marks VALUES(?,?,?,?,?)",
                        (
                            student_id,
                            course_id,
                            exam["exam_type"],
                            round(maximum * (0.35 + (i + j) % 13 * 0.05), 1),
                            maximum,
                        ),
                    )
        if connection.execute("PRAGMA foreign_key_check").fetchone():
            raise ValueError("Sample data has invalid relationships.")
    return sample_counts()


def backup_database():
    if not DB.exists():
        return None
    folder = DB.parent / "backups"
    folder.mkdir(exist_ok=True)
    target = (
        folder
        / f"campusbuddy-before-expansion-{datetime.now().strftime('%Y%m%d-%H%M%S-%f')}.db"
    )
    with connect() as source, sqlite3.connect(target) as dest:
        source.backup(dest)
    return target


if __name__ == "__main__":
    backup = backup_database()
    if backup:
        print("Backup:", backup)
    print(json.dumps(seed_sample_data(), indent=2))
