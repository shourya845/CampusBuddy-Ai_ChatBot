def spec(name, desc, properties, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
                "additionalProperties": False,
            },
        },
    }


S = {"type": "string"}
SCHEMAS = [
    spec(
        "mark_attendance",
        "Propose BULK attendance for enrolled roster: all present except absent_rolls. No write until user clicks confirmation.",
        {
            "course_id": S,
            "class_date": S,
            "absent_rolls": {"type": "array", "items": {"type": "integer"}},
        },
        ["course_id", "class_date", "absent_rolls"],
    ),
    spec(
        "get_attendance_percentage",
        "Get own attendance or teacher-authorized student attendance; omit course_id for every subject.",
        {"student_id": S, "course_id": S},
        [],
    ),
    spec(
        "list_shortage_students",
        "Teacher only: list enrolled students below 75 percent.",
        {"course_id": S},
        ["course_id"],
    ),
    spec(
        "classes_needed_for_target",
        "Consecutive classes needed with planned feasibility. Defaults to 75 percent.",
        {"course_id": S, "student_id": S, "target": {"type": "number"}},
        ["course_id"],
    ),
    spec(
        "add_marks",
        "Propose one score for an existing MID/FINAL exam; user must confirm. max_score must match exam definition.",
        {
            "student_id": S,
            "course_id": S,
            "exam_type": {"type": "string", "enum": ["QUIZ", "MID", "FINAL"]},
            "score": {"type": "number"},
            "max_score": {"type": "number"},
        },
        ["student_id", "course_id", "exam_type", "score", "max_score"],
    ),
    spec(
        "get_report_card",
        "All enrolled courses with attendance, marks, weighted percentage and simple grade.",
        {"student_id": S},
        [],
    ),
]
TOOL_NAMES = {s["function"]["name"] for s in SCHEMAS}
WRITES = {"mark_attendance", "add_marks"}
