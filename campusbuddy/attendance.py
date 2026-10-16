import math

from .permissions import accessible_courses
from .proposals import create_proposal
from .settings import ATTENDANCE_TARGET, today


def recovery(present, total, remaining, target=ATTENDANCE_TARGET):
    if (
        any((type(v) is not int or v < 0 for v in (present, total, remaining)))
        or present > total
    ):
        raise ValueError("Invalid attendance counts")
    if (
        type(target) not in (int, float)
        or not math.isfinite(target)
        or (not 0 < target <= 100)
    ):
        raise ValueError("Target must be greater than 0 and at most 100")
    if target == 100:
        needed = 0 if present == total and total else 1 if not total else None
    else:
        needed = max(
            0, math.ceil((target * total - 100 * present) / (100 - target) - 1e-10)
        )
    if total == 0 and needed == 0:
        needed = 1
    return {
        "present": present,
        "held": total,
        "percentage": round(100 * present / total, 2) if total else None,
        "target": target,
        "consecutive_classes_needed": needed,
        "remaining_planned_classes": remaining,
        "recovery_feasible": needed is not None and needed <= remaining,
        "maximum_final_percentage": round(
            100 * (present + remaining) / (total + remaining), 2
        )
        if total + remaining
        else None,
        "safe_absences_now": max(0, math.floor(100 * present / target - total))
        if total
        else 0,
    }


def attendance(connection, student_id, course, target=ATTENDANCE_TARGET):
    row = connection.execute(
        "SELECT COUNT(*) n,COALESCE(SUM(CASE WHEN a.status='P' THEN 1 ELSE 0 END),0) p,COUNT(a.status) recorded FROM class_sessions cl LEFT JOIN attendance a ON a.course_id=cl.course_id AND a.class_date=cl.class_date AND a.student_id=? WHERE cl.course_id=? AND cl.class_date<=?",
        (student_id, course["course_id"], today().isoformat()),
    ).fetchone()
    result = recovery(
        int(row["p"]),
        row["n"],
        max(0, course["total_planned_classes"] - row["n"]),
        target,
    )
    result.update(
        course_id=course["course_id"],
        course=course["name"],
        student_id=student_id,
        unrecorded_classes=row["n"] - row["recorded"],
    )
    result["message"] = (
        "Target is impossible with the remaining planned classes."
        if not result["recovery_feasible"]
        else f"Attend the next {result['consecutive_classes_needed']} consecutive classes to reach {target}%."
    )
    if result["unrecorded_classes"]:
        result["missing_policy"] = (
            "Unrecorded held classes conservatively count as absent; ask your teacher to correct them."
        )
    return result


def mark_attendance(connection, user, course, student_id, arguments):
    return create_proposal(connection, user, "mark_attendance", arguments)


def get_attendance_percentage(connection, user, course, student_id, arguments):
    courses = accessible_courses(connection, user, student_id, course)
    return {
        "student_id": student_id,
        "courses": [attendance(connection, student_id, course) for course in courses],
        "scope": "Own records"
        if user["role"] == "student"
        else "Only courses assigned to signed-in teacher",
    }


def classes_needed_for_target(connection, user, course, student_id, arguments):
    return attendance(
        connection, student_id, course, arguments.get("target", ATTENDANCE_TARGET)
    )


def list_shortage_students(connection, user, course, student_id, arguments):
    students = connection.execute(
        "SELECT students.student_id,students.roll_no,students.name FROM students JOIN enrollments ON enrollments.student_id=students.student_id WHERE enrollments.course_id=? ORDER BY students.roll_no",
        (course["course_id"],),
    ).fetchall()
    shortage = []
    for student_record in students:
        summary = attendance(connection, student_record["student_id"], course)
        if (
            summary["held"]
            and 100 * summary["present"] < ATTENDANCE_TARGET * summary["held"]
        ):
            shortage.append({**dict(student_record), **summary})
    return {"course": course["name"], "below_75": shortage, "count": len(shortage)}
