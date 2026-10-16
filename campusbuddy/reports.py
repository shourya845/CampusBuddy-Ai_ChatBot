from .attendance import attendance
from .marks import progress
from .permissions import accessible_courses


def get_report_card(connection, user, course, student_id, arguments):
    courses = accessible_courses(connection, user, student_id, course)
    report = []
    for course in courses:
        summary = attendance(connection, student_id, course)
        summary.update(progress(connection, student_id, course["course_id"]))
        report.append(summary)
    return {
        "student_id": student_id,
        "courses": report,
        "scope": "Own records"
        if user["role"] == "student"
        else "Only courses assigned to signed-in teacher",
    }
