import re

from .permissions import directory
from .settings import today


def demo_route(text, actor, state):
    request_text = text.lower()
    directory_data = directory(actor)
    course_id = None
    for course in directory_data["courses"]:
        if (
            course["name"].lower() in request_text
            or re.search(
                "\\b" + re.escape(course["course_code"].lower()) + "\\b", request_text
            )
            or course["course_id"].lower() in request_text
        ):
            course_id = course["course_id"]
    student_id = actor["id"] if actor["role"] == "student" else None
    match = re.search("\\bS\\d{3}\\b", text, re.I)
    if match:
        student_id = match[0].upper()
    if "mark attendance" in request_text or "all present" in request_text:
        if not course_id:
            return (None, None, "Which course should I mark attendance for?")
        day = today().isoformat() if "today" in request_text else None
        date_match = re.search("\\d{4}-\\d{2}-\\d{2}", request_text)
        if date_match:
            day = date_match[0]
        if not day:
            return (None, None, "What class date (YYYY-MM-DD) should I use?")
        if "all present" not in request_text:
            return (
                None,
                None,
                "Should I mark all present, or all present except which roll numbers?",
            )
        rolls = (
            [int(x) for x in re.findall("\\d+", request_text.split("except", 1)[1])]
            if "except" in request_text
            else []
        )
        return (
            "mark_attendance",
            {"course_id": course_id, "class_date": day, "absent_rolls": rolls},
            None,
        )
    if "below" in request_text or "shortage" in request_text:
        return (
            ("list_shortage_students", {"course_id": course_id}, None)
            if course_id
            else (None, None, "Which course should I check for shortage?")
        )
    if (
        "how many" in request_text
        or "reach" in request_text
        or "more classes" in request_text
    ):
        if not course_id:
            return (None, None, "Which course and target percentage should I check?")
        if not student_id:
            return (None, None, "Which student ID should I check?")
        target = re.search("(\\d+(?:\\.\\d+)?)\\s*%", request_text)
        return (
            "classes_needed_for_target",
            {
                "student_id": student_id,
                "course_id": course_id,
                "target": float(target[1]) if target else 75,
            },
            None,
        )
    if "attendance" in request_text:
        if not student_id:
            return (None, None, "Which student ID should I check?")
        return (
            "get_attendance_percentage",
            {
                "student_id": student_id,
                **({"course_id": course_id} if course_id else {}),
            },
            None,
        )
    if "report" in request_text or "marks" in request_text:
        if not student_id:
            return (None, None, "Which student ID should I check?")
        return ("get_report_card", {"student_id": student_id}, None)
    return (
        None,
        None,
        "Demo mode supports the five judge prompts and report cards. Use the structured tools tab for marks entry, or configure the hosted model endpoint and API key for full conversational tool calling.",
    )
