import math
from datetime import date

from .permissions import allowed, student, user_for
from .settings import today
from .tool_schemas import SCHEMAS, TOOL_NAMES, WRITES


def validate(connection, actor, name, arguments):
    if name not in TOOL_NAMES:
        raise ValueError("Unknown tool.")
    schema = next(
        (s["function"]["parameters"] for s in SCHEMAS if s["function"]["name"] == name)
    )
    if (
        not isinstance(arguments, dict)
        or set(arguments) - set(schema["properties"])
        or set(schema["required"]) - set(arguments)
    ):
        raise ValueError(
            "Missing or unexpected fields. Please provide the required details."
        )
    for field, value in arguments.items():
        field_schema = schema["properties"][field]
        field_type = field_schema["type"]
        if field_type == "string" and (not isinstance(value, str) or not value.strip()):
            raise ValueError(field + " must be a nonempty string.")
        if field_type == "number" and (
            type(value) not in (int, float) or not math.isfinite(value)
        ):
            raise ValueError(field + " must be a finite number.")
        if field_type == "array" and (
            not isinstance(value, list)
            or any((type(x) is not int or x <= 0 for x in value))
        ):
            raise ValueError("Absent rolls must be positive integers.")
        if "enum" in field_schema and value not in field_schema["enum"]:
            raise ValueError("Invalid " + field)
    user = user_for(connection, actor)
    course = None
    student_id = None
    if name in (
        "get_attendance_percentage",
        "classes_needed_for_target",
        "add_marks",
        "get_report_card",
    ):
        student_id = student(connection, user, arguments)
    if arguments.get("course_id"):
        course = allowed(
            connection,
            user,
            arguments["course_id"],
            student_id or (user["id"] if user["role"] == "student" else None),
            name in WRITES,
        )
    if name == "list_shortage_students" and user["role"] != "teacher":
        raise PermissionError("Only the course teacher can view the shortage list.")
    if name == "mark_attendance":
        class_date = date.fromisoformat(arguments["class_date"])
        if arguments["class_date"] != class_date.isoformat():
            raise ValueError("Use YYYY-MM-DD for the date.")
        if class_date > today():
            raise ValueError("Future attendance cannot be marked.")
        roster = [
            dict(record)
            for record in connection.execute(
                "SELECT s.student_id,s.roll_no FROM students s JOIN enrollments e ON e.student_id=s.student_id WHERE e.course_id=?",
                (arguments["course_id"],),
            )
        ]
        if not roster:
            raise ValueError("This course has no enrolled students.")
        if set(arguments["absent_rolls"]) - {record["roll_no"] for record in roster}:
            raise ValueError(
                "One or more absent rolls are not enrolled. No changes proposed."
            )
        exists = connection.execute(
            "SELECT 1 FROM class_sessions WHERE course_id=? AND class_date=?",
            (arguments["course_id"], arguments["class_date"]),
        ).fetchone()
        count = connection.execute(
            "SELECT COUNT(*) FROM class_sessions WHERE course_id=?",
            (arguments["course_id"],),
        ).fetchone()[0]
        if not exists and count >= course["total_planned_classes"]:
            raise ValueError(
                "Planned class limit reached. Ask the administrator to review the course plan."
            )
    if name == "add_marks":
        exam = connection.execute(
            "SELECT max_score FROM exams WHERE course_id=? AND exam_type=?",
            (arguments["course_id"], arguments["exam_type"]),
        ).fetchone()
        if not exam:
            raise ValueError("Exam is not configured. Seed includes MID and FINAL.")
        if arguments["max_score"] != exam[0]:
            raise ValueError(f"This exam is out of {exam[0]}. Please use that maximum.")
        if not 0 <= arguments["score"] <= arguments["max_score"]:
            raise ValueError("Score must be between 0 and max_score.")
    return (user, course, student_id)
