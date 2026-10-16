import json
import time

from .database import connect
from .settings import PROPOSAL_EXPIRY_SECONDS
from .validation import validate


def confirm(actor, token, approve):
    if type(approve) is not bool:
        raise ValueError("Confirmation must be a user decision.")
    with connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT * FROM pending WHERE id=? AND actor=?", (token, actor["id"])
        ).fetchone()
        if not row or row["used"]:
            raise ValueError("Proposal unavailable or already resolved.")
        if time.time() - row["created"] > PROPOSAL_EXPIRY_SECONDS:
            raise ValueError("Proposal expired. Please submit again.")
        arguments = json.loads(row["args"])
        name = row["tool"]
        validate(connection, actor, name, arguments)
        connection.execute("UPDATE pending SET used=1 WHERE id=?", (token,))
        if not approve:
            return {"status": "cancelled", "message": "No attendance or marks changed."}
        if name == "mark_attendance":
            connection.execute(
                "INSERT OR IGNORE INTO class_sessions VALUES(?,?)",
                (arguments["course_id"], arguments["class_date"]),
            )
            roster = connection.execute(
                "SELECT s.student_id,s.roll_no FROM students s JOIN enrollments e ON e.student_id=s.student_id WHERE e.course_id=?",
                (arguments["course_id"],),
            ).fetchall()
            connection.executemany(
                "INSERT INTO attendance VALUES(?,?,?,?) ON CONFLICT(student_id,course_id,class_date) DO UPDATE SET status=excluded.status",
                [
                    (
                        record["student_id"],
                        arguments["course_id"],
                        arguments["class_date"],
                        "A" if record["roll_no"] in arguments["absent_rolls"] else "P",
                    )
                    for record in roster
                ],
            )
        else:
            connection.execute(
                "INSERT INTO marks VALUES(?,?,?,?,?) ON CONFLICT(student_id,course_id,exam_type) DO UPDATE SET score=excluded.score,max_score=excluded.max_score",
                (
                    arguments["student_id"],
                    arguments["course_id"],
                    arguments["exam_type"],
                    arguments["score"],
                    arguments["max_score"],
                ),
            )
        connection.execute(
            "INSERT INTO audit(actor,tool,args,created) VALUES(?,?,?,?)",
            (actor["id"], name, json.dumps(arguments), time.time()),
        )
        return {"status": "saved", "tool": name, "change": arguments}
