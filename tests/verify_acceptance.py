import argparse
import copy
import json
import sqlite3
import tempfile
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import campusbuddy.database as database
from campusbuddy.agent import reply
from campusbuddy.confirmation import confirm
from campusbuddy.model import connect_model, model_error_message
from campusbuddy.settings import GROQ_MODEL, INTRO, ROOT, today
from campusbuddy.tool_registry import execute

REQUEST_PAUSE_SECONDS = 35
LAST_REQUEST_AT = 0.0

TEACHER = {"id": "T001", "name": "Dr. Sharma", "role": "teacher"}
STUDENT = {"id": "S001", "name": "Aarav", "role": "student"}


def timestamp():
    return datetime.now(ZoneInfo("Asia/Kolkata")).isoformat()


def run_prompt(provider, actor, text, state=None):
    global LAST_REQUEST_AT
    state = {} if state is None else state
    saved = copy.deepcopy(state)
    print("Checking " + actor["role"] + ": " + text, flush=True)
    for attempt in range(3):
        wait = max(0, REQUEST_PAUSE_SECONDS - (time.monotonic() - LAST_REQUEST_AT))
        if wait:
            print("Spacing hosted requests for the free-tier limit.", flush=True)
            time.sleep(wait)
        state.clear()
        state.update(copy.deepcopy(saved))
        before = len(state.get("trace", []))
        answer = reply(text, actor, state, provider=provider)
        LAST_REQUEST_AT = time.monotonic()
        error = state.get("last_model_error", {})
        if error.get("status_code") == 429 and attempt < 2:
            print(
                "Provider rate limit: retrying this check after the pacing interval.",
                flush=True,
            )
            continue
        trace = state.get("trace", [])[before:]
        if any("error" in event["result"] for event in trace):
            raise AssertionError("A database tool returned an error.")
        if any(
            term in answer.lower()
            for term in (
                "no remaining inference credits",
                "hosted model is unavailable",
                "rejected the api token",
                "rate limit was reached",
                "tool-step limit",
            )
        ):
            raise AssertionError(answer)
        return state, {
            "role": actor["role"],
            "prompt": text,
            "actual_reply": answer,
            "tools": trace,
        }
    raise AssertionError("The provider rate limit prevented the live request.")


def record_mandatory(evidence, record):
    evidence["mandatory_prompts"].append(record)
    folder = ROOT / "docs" / "evidence"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "live_acceptance_progress.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    if len(evidence["mandatory_prompts"]) == 5:
        write_success(evidence)


def require_tool(state, name):
    results = [
        event["result"] for event in state.get("trace", []) if event["tool"] == name
    ]
    if not results:
        raise AssertionError("Expected a real " + name + " tool invocation.")
    return results[-1]


def verify(provider):
    evidence = {
        "executed_at": timestamp(),
        "provider": provider,
        "model": GROQ_MODEL,
        "status": "running",
        "mandatory_prompts": [],
        "additional_checks": [],
    }
    model = connect_model(provider=provider)
    introduction = model.invoke(
        "Introduce yourself in one sentence as CampusBuddy, an attendance and academic progress assistant."
    )
    assert "CampusBuddy" in str(introduction.content)
    assert "CampusBuddy" in INTRO
    evidence["model_introduction"] = introduction.content
    original_database = database.DB
    with tempfile.TemporaryDirectory() as folder:
        temporary_database = Path(folder) / "judge.db"
        with (
            database.connect() as source,
            sqlite3.connect(temporary_database) as destination,
        ):
            source.backup(destination)
        destination.close()
        database.DB = temporary_database
        try:
            with database.connect() as connection:
                before_count = connection.execute(
                    "SELECT COUNT(*) FROM attendance"
                ).fetchone()[0]
            state, record = run_prompt(
                provider,
                TEACHER,
                "Mark attendance for DBMS today - all present except roll 5 and 12.",
            )
            proposal = require_tool(state, "mark_attendance")
            change = proposal["proposed_change"]
            assert proposal["status"] == "confirmation_required"
            assert (
                change["course_id"] == "C001"
                and change["class_date"] == today().isoformat()
            )
            assert set(change["absent_rolls"]) == {5, 12}
            assert proposal["present"] == 198 and proposal["absent"] == 2
            with database.connect() as connection:
                assert (
                    connection.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
                    == before_count
                )
            record["explicit_confirmation"] = confirm(
                TEACHER, proposal["proposal_id"], True
            )
            assert record["explicit_confirmation"]["status"] == "saved"
            with database.connect() as connection:
                rows = connection.execute(
                    "SELECT status,COUNT(*) FROM attendance WHERE course_id=? AND class_date=? GROUP BY status",
                    ("C001", today().isoformat()),
                ).fetchall()
                assert {row[0]: row[1] for row in rows} == {"A": 2, "P": 198}
            record_mandatory(evidence, record)

            state, record = run_prompt(provider, TEACHER, "Who is below 75% in DBMS?")
            shortage = require_tool(state, "list_shortage_students")
            assert shortage["count"] > 0 and all(
                row["percentage"] < 75 for row in shortage["below_75"]
            )
            record_mandatory(evidence, record)

            state, record = run_prompt(
                provider, STUDENT, "What is my attendance in every subject?"
            )
            attendance = require_tool(state, "get_attendance_percentage")
            assert len(attendance["courses"]) == 5
            assert all(row["student_id"] == "S001" for row in attendance["courses"])
            assert any(not row["recovery_feasible"] for row in attendance["courses"])
            record_mandatory(evidence, record)

            state, record = run_prompt(
                provider,
                STUDENT,
                "How many more classes must I attend to reach 75% in Operating Systems?",
            )
            recovery = require_tool(state, "classes_needed_for_target")
            assert "8" in record["actual_reply"]
            assert (
                recovery["course_id"] == "C002"
                and recovery["consecutive_classes_needed"] == 8
            )
            record_mandatory(evidence, record)

            state, record = run_prompt(provider, STUDENT, "Show me Rahul's marks.")
            assert "cannot share" in record["actual_reply"].lower()
            assert not state.get("trace")
            record_mandatory(evidence, record)

            state, record = run_prompt(
                provider, STUDENT, "Show my report card for all subjects."
            )
            report = require_tool(state, "get_report_card")
            assert len(report["courses"]) == 5 and all(
                course["grade"] for course in report["courses"]
            )
            evidence["additional_checks"].append(record)

            state, record = run_prompt(
                provider, TEACHER, "Enter 42 out of 50 for S001 in DBMS MID."
            )
            proposal = require_tool(state, "add_marks")
            assert proposal["proposed_change"]["score"] == 42
            _, cancellation = run_prompt(provider, TEACHER, "cancel it", state)
            assert state["pending"] is None
            record["session_cancellation"] = cancellation["actual_reply"]
            evidence["additional_checks"].append(record)

            state, record = run_prompt(
                provider,
                TEACHER,
                "Mark attendance for DBMS - all present except roll 5.",
            )
            assert not state.get("pending")
            assert any(
                word in record["actual_reply"].lower() for word in ("date", "when")
            )
            evidence["additional_checks"].append(record)

            for title, actor, tool, arguments in [
                (
                    "Other student access",
                    STUDENT,
                    "get_report_card",
                    {"student_id": "S003"},
                ),
                (
                    "Wrong teacher",
                    {"id": "T002", "role": "teacher"},
                    "mark_attendance",
                    {
                        "course_id": "C001",
                        "class_date": today().isoformat(),
                        "absent_rolls": [],
                    },
                ),
                (
                    "Score above maximum",
                    TEACHER,
                    "add_marks",
                    {
                        "student_id": "S001",
                        "course_id": "C001",
                        "exam_type": "MID",
                        "score": 51,
                        "max_score": 50,
                    },
                ),
            ]:
                try:
                    execute(actor, tool, arguments)
                except (PermissionError, ValueError) as error:
                    evidence["additional_checks"].append(
                        {
                            "check": title,
                            "actual_reply": str(error),
                            "status": "blocked_as_required",
                        }
                    )
                else:
                    raise AssertionError(title + " was not blocked.")
            with database.connect() as connection:
                assert (
                    connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
                )
                assert not connection.execute("PRAGMA foreign_key_check").fetchall()
            evidence["status"] = "passed"
            evidence["production_database_changed"] = False
            return evidence
        finally:
            database.DB = original_database


def write_success(evidence):
    folder = ROOT / "docs" / "evidence"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "live_acceptance.json").write_text(
        json.dumps(evidence, indent=2), encoding="utf-8"
    )
    lines = [
        "# Mandatory judge prompts - actual live replies",
        "",
        f"Executed: {evidence['executed_at']}",
        f"Provider: {evidence['provider']}; model: {evidence['model']}",
        "All requests used the real hosted model and database tools. Confirmation was explicitly simulated in a temporary copy; the application database was unchanged.",
        "",
        f"Model introduction: {evidence['model_introduction']}",
        "",
    ]
    for index, record in enumerate(evidence["mandatory_prompts"], 1):
        lines.extend(
            [
                f"## {index}. {record['role'].title()}",
                "Prompt: " + record["prompt"],
                "",
                "Actual reply:",
                "",
                record["actual_reply"],
                "",
            ]
        )
        if record.get("explicit_confirmation"):
            lines.extend(
                [
                    "Explicit confirmation result:",
                    "```json",
                    json.dumps(record["explicit_confirmation"], indent=2),
                    "```",
                    "",
                ]
            )
    lines.extend(["## Additional rule and session checks", ""])
    for record in evidence["additional_checks"]:
        lines.extend(
            [
                "### " + record.get("prompt", record.get("check", "Check")),
                record["actual_reply"],
                "",
            ]
        )
        if record.get("session_cancellation"):
            lines.extend(["Follow-up: cancel it", record["session_cancellation"], ""])
    (ROOT / "test_prompts.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["groq"], default="groq")
    parser.add_argument("--pause-seconds", type=float, default=35)
    arguments = parser.parse_args()
    global REQUEST_PAUSE_SECONDS
    REQUEST_PAUSE_SECONDS = max(0, arguments.pause_seconds)
    try:
        evidence = verify(arguments.provider)
        write_success(evidence)
    except Exception as error:
        evidence = {
            "executed_at": timestamp(),
            "provider": arguments.provider,
            "status": "not_passed",
            "error_type": type(error).__name__,
            "http_status": getattr(error, "status_code", None),
            "message": model_error_message(error)
            if getattr(error, "status_code", None)
            else "The live acceptance workflow did not finish. See the failed check; no successful transcript was fabricated.",
            "production_database_changed": False,
        }
        folder = ROOT / "docs" / "evidence"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "live_acceptance_status.json").write_text(
            json.dumps(evidence, indent=2), encoding="utf-8"
        )
        print(json.dumps(evidence))
        return 1
    (ROOT / "docs" / "evidence" / "live_acceptance_status.json").write_text(
        json.dumps(
            {
                "executed_at": timestamp(),
                "provider": arguments.provider,
                "status": "passed",
                "production_database_changed": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "passed",
                "provider": arguments.provider,
                "mandatory_prompts": 5,
                "production_database_changed": False,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
