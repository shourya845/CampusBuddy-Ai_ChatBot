import json
import time
import uuid


def create_proposal(connection, user, tool_name, arguments):
    proposal_id = uuid.uuid4().hex
    connection.execute(
        "INSERT INTO pending VALUES(?,?,?,?,?,0)",
        (proposal_id, user["id"], tool_name, json.dumps(arguments), time.time()),
    )
    result = {
        "status": "confirmation_required",
        "proposal_id": proposal_id,
        "tool": tool_name,
        "proposed_change": arguments,
        "message": "No attendance or marks changed. Review and click Confirm change. Expires in 10 minutes.",
    }
    if tool_name == "mark_attendance":
        total_students = connection.execute(
            "SELECT COUNT(*) FROM enrollments WHERE course_id=?",
            (arguments["course_id"],),
        ).fetchone()[0]
        absent_students = len(set(arguments["absent_rolls"]))
        result.update(
            total_students=total_students,
            absent=absent_students,
            present=total_students - absent_students,
        )
    return result
