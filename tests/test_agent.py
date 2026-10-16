from unittest.mock import patch

import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage

import campusbuddy.database as db
from campusbuddy.agent import reply
from campusbuddy.model import make_tool, trim_history
from campusbuddy.tool_schemas import SCHEMAS


class ToolModel(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kwargs):
        return self


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB", tmp_path / "agent.db")
    db.initialize(25, 3, 4)


def test_langchain_executes_database_tool(isolated):
    model = ToolModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {"id": "call_1", "name": "get_attendance_percentage", "args": {}}
                ],
            ),
            AIMessage(content="Database attendance retrieved."),
        ]
    )
    state = {}
    with patch("campusbuddy.model.ChatGroq", return_value=model) as constructor:
        answer = reply(
            "My attendance?",
            {"id": "S001", "role": "student"},
            state,
            api_key="test-only",
            provider="groq",
        )
    assert answer == "Database attendance retrieved."
    assert constructor.call_args.kwargs["model"] == "openai/gpt-oss-20b"
    assert state["trace"][0]["result"]["courses"][0]["percentage"] == 60
    assert state["history"][2]["role"] == "tool"
    assert len(state["trace"][0]["result"]["courses"]) == 4


def test_live_path_privacy_guard_without_network(isolated):
    with patch("campusbuddy.model.ChatGroq") as model:
        answer = reply(
            "Show me Rahul's marks.",
            {"id": "S001", "role": "student"},
            {},
            api_key="test-only",
            provider="groq",
        )
        assert "cannot share" in answer
        model.assert_not_called()


def test_api_failure_friendly(isolated):
    with patch("campusbuddy.model.ChatGroq", side_effect=RuntimeError("network")):
        answer = reply(
            "My attendance?",
            {"id": "S001", "role": "student"},
            {},
            api_key="test-only",
            provider="groq",
        )
        assert "unavailable" in answer


def test_langchain_write_only_proposes_and_cancel_uses_session(isolated):
    model = ToolModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "id": "call_1",
                        "name": "add_marks",
                        "args": {
                            "student_id": "S001",
                            "course_id": "C001",
                            "exam_type": "MID",
                            "score": 49,
                            "max_score": 50,
                        },
                    }
                ],
            ),
            AIMessage(content="Please confirm this marks change."),
        ]
    )
    state = {}
    teacher = {"id": "T001", "role": "teacher"}
    with patch("campusbuddy.model.ChatGroq", return_value=model):
        reply(
            "Enter 49/50 in MID for S001 in DBMS.",
            teacher,
            state,
            api_key="test-only",
            provider="groq",
        )
    assert state["pending"]["status"] == "confirmation_required"
    with db.connect() as c:
        assert (
            c.execute(
                "SELECT score FROM marks WHERE student_id='S001' AND course_id='C001' AND exam_type='MID'"
            ).fetchone()[0]
            != 49
        )
    reply("cancel it", teacher, state, api_key="test-only")
    assert state["pending"] is None


def test_langchain_tool_identity_is_bound_to_session(isolated):
    state = {"trace": [], "pending": None}
    definition = next(
        (d for d in SCHEMAS if d["function"]["name"] == "get_report_card")
    )
    tool = make_tool(definition, {"id": "S001", "role": "student"}, state)
    result = tool.invoke({"student_id": "S003"})
    assert "own records" in result
    assert "actor" not in tool.args


def test_history_trim_keeps_complete_turns():
    history = [
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "old"},
        {"role": "user", "content": "new"},
        {"role": "assistant", "content": "new"},
    ]
    trim_history(history, limit=3)
    assert history == [
        {"role": "user", "content": "new"},
        {"role": "assistant", "content": "new"},
    ]


def test_missing_attendance_date_asks_without_model(isolated):
    with patch("campusbuddy.model.ChatGroq") as model:
        state = {}
        answer = reply(
            "Mark attendance for DBMS - all present except roll 5.",
            {"id": "T001", "role": "teacher"},
            state,
            provider="groq",
        )
        assert "date" in answer.lower()
        assert not state["pending"]
        model.assert_not_called()


def test_teacher_model_context_only_sends_referenced_students(isolated):
    from campusbuddy.model import model_directory

    context = model_directory(
        {"id": "T001", "role": "teacher"},
        {"history": [{"role": "user", "content": "Enter MID marks for S001 in DBMS."}]},
    )
    assert context["authorized_student_count"] == 25
    assert [student["student_id"] for student in context["referenced_students"]] == [
        "S001"
    ]


def test_model_shortage_summary_preserves_database_results(isolated):
    from campusbuddy.model import model_tool_result
    from campusbuddy.tool_registry import execute

    result = execute(
        {"id": "T001", "role": "teacher"},
        "list_shortage_students",
        {"course_id": "C001"},
    )
    compact = model_tool_result("list_shortage_students", result)
    assert compact["count"] == result["count"]
    assert [student["percentage"] for student in compact["below_75"]] == [
        student["percentage"] for student in result["below_75"]
    ]
    assert "recovery_feasible" in result["below_75"][0]
    assert "recovery_feasible" not in compact["below_75"][0]
