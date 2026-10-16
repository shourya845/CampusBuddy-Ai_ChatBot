from .attendance import (
    classes_needed_for_target,
    get_attendance_percentage,
    list_shortage_students,
    mark_attendance,
)
from .database import connect
from .marks import add_marks
from .reports import get_report_card
from .validation import validate

TOOL_HANDLERS = {
    function.__name__: function
    for function in (
        mark_attendance,
        get_attendance_percentage,
        list_shortage_students,
        classes_needed_for_target,
        add_marks,
        get_report_card,
    )
}


def execute(actor, name, arguments):
    with connect() as connection:
        (user, course, student_id) = validate(connection, actor, name, arguments)
        return TOOL_HANDLERS[name](connection, user, course, student_id, arguments)


def safe_execute(actor, name, arguments):
    try:
        return execute(actor, name, arguments)
    except (ValueError, PermissionError, TypeError) as e:
        return {"error": str(e)}
    except Exception:
        return {
            "error": "The database request could not be completed. Please retry or contact the organizer."
        }
