from .proposals import create_proposal
from .settings import GRADE_BOUNDARIES


def progress(connection, student_id, course_id):
    rows = [
        dict(record)
        for record in connection.execute(
            "SELECT e.exam_type,e.max_score,m.score FROM exams e LEFT JOIN marks m ON m.course_id=e.course_id AND m.exam_type=e.exam_type AND m.student_id=? WHERE e.course_id=? ORDER BY e.exam_type",
            (student_id, course_id),
        )
    ]
    recorded = [record for record in rows if record["score"] is not None]
    percentage = (
        100
        * sum((record["score"] for record in recorded))
        / sum((record["max_score"] for record in recorded))
        if recorded
        else None
    )
    grade = (
        "Pending"
        if percentage is None
        else next(
            (
                grade_label
                for (minimum_percentage, grade_label) in GRADE_BOUNDARIES
                if percentage >= minimum_percentage
            )
        )
    )
    return {
        "exams": rows,
        "weighted_percentage": round(percentage, 2) if percentage is not None else None,
        "grade": grade,
        "missing_exams": len(rows) - len(recorded),
    }


def add_marks(connection, user, course, student_id, arguments):
    return create_proposal(connection, user, "add_marks", arguments)
