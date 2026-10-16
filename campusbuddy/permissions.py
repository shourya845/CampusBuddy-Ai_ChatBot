import re

from .database import connect


def user_for(connection, actor):
    row = connection.execute(
        "SELECT id,role FROM users WHERE id=?", (actor.get("id"),)
    ).fetchone()
    if not row:
        raise PermissionError("Please sign in again.")
    return row


def allowed(connection, user, course_id, student_id=None, write=False):
    course = connection.execute(
        "SELECT * FROM courses WHERE course_id=?", (course_id,)
    ).fetchone()
    if not course:
        raise ValueError("Unknown course ID. Please choose a course from the sidebar.")
    if user["role"] == "teacher":
        if course["teacher_id"] != user["id"]:
            raise PermissionError(
                "Only the assigned teacher may access or change this course."
            )
    elif write or student_id != user["id"]:
        raise PermissionError(
            "Sorry, students can only view their own data and cannot change records."
        )
    if student_id and (
        not connection.execute(
            "SELECT 1 FROM enrollments WHERE student_id=? AND course_id=?",
            (student_id, course_id),
        ).fetchone()
    ):
        raise ValueError("Student is not enrolled in this course.")
    return course


def student(connection, user, arguments):
    student_id = arguments.get("student_id")
    if user["role"] == "student":
        if student_id and student_id != user["id"]:
            raise PermissionError(
                "Sorry, I cannot share another student's marks or attendance. You can view only your own records."
            )
        return user["id"]
    if not student_id:
        raise ValueError("Which student? Please provide a student ID.")
    if not connection.execute(
        "SELECT 1 FROM students WHERE student_id=?", (student_id,)
    ).fetchone():
        raise ValueError("Unknown student ID.")
    return student_id


def directory(actor):
    with connect() as connection:
        if actor["role"] == "teacher":
            courses = [
                dict(record)
                for record in connection.execute(
                    "SELECT * FROM courses WHERE teacher_id=?", (actor["id"],)
                )
            ]
            students = [
                dict(record)
                for record in connection.execute(
                    "SELECT DISTINCT s.student_id,s.roll_no,s.name FROM students s JOIN enrollments e ON e.student_id=s.student_id JOIN courses co ON co.course_id=e.course_id WHERE co.teacher_id=?",
                    (actor["id"],),
                )
            ]
        else:
            courses = [
                dict(record)
                for record in connection.execute(
                    "SELECT co.* FROM courses co JOIN enrollments e ON co.course_id=e.course_id WHERE e.student_id=?",
                    (actor["id"],),
                )
            ]
            students = [
                dict(record)
                for record in connection.execute(
                    "SELECT student_id,roll_no,name FROM students WHERE student_id=?",
                    (actor["id"],),
                )
            ]
    return {"courses": courses, "students": students}


def privacy_refusal(text, actor):
    if actor["role"] != "student":
        return None
    lowered = text.lower()
    with connect() as connection:
        others = connection.execute(
            "SELECT student_id,roll_no,name FROM students WHERE student_id<>?",
            (actor["id"],),
        ).fetchall()
    for other in others:
        if (
            re.search("\\b" + re.escape(other["name"].lower()) + "\\b", lowered)
            or re.search(
                "\\b" + re.escape(other["student_id"].lower()) + "\\b", lowered
            )
            or re.search("\\broll\\s*" + str(other["roll_no"]) + "\\b", lowered)
        ):
            return "Sorry, I cannot share another student's marks or attendance. You can view only your own records."
    return None


def accessible_courses(connection, user, student_id, course=None):
    courses = (
        [course]
        if course
        else connection.execute(
            "SELECT courses.* FROM courses JOIN enrollments ON enrollments.course_id=courses.course_id WHERE enrollments.student_id=? ORDER BY courses.course_id",
            (student_id,),
        ).fetchall()
    )
    accessible = []
    for course in courses:
        if user["role"] == "teacher" and course["teacher_id"] != user["id"]:
            continue
        allowed(connection, user, course["course_id"], student_id)
        accessible.append(course)
    return accessible
