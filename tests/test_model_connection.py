import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

import pytest

import campusbuddy.database as db
from campusbuddy.agent import reply
from campusbuddy.model import ModelConfigurationError, connect_model
from campusbuddy.settings import GROQ_MODEL


def test_missing_api_key_is_explained(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ModelConfigurationError, match="GROQ_API_KEY"):
        connect_model(provider="groq")


def test_unknown_provider_is_rejected():
    with pytest.raises(ModelConfigurationError, match="Groq API"):
        connect_model("test-only", provider="unsupported")


def test_groq_remains_an_explicit_option():
    with patch("campusbuddy.model.ChatGroq") as model:
        connect_model("test-only", provider="groq")
    assert model.call_args.kwargs["model"] == GROQ_MODEL


def test_groq_http_tool_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB", tmp_path / "http.db")
    db.initialize(25, 3, 4)
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append(payload)
            if len(requests) == 1:
                message = {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "attendance_1",
                            "type": "function",
                            "function": {
                                "name": "get_attendance_percentage",
                                "arguments": "{}",
                            },
                        }
                    ],
                }
                finish = "tool_calls"
            else:
                message = {
                    "role": "assistant",
                    "content": "Attendance checked successfully.",
                }
                finish = "stop"
            response = {
                "id": "test-completion",
                "object": "chat.completion",
                "created": 1,
                "model": GROQ_MODEL,
                "choices": [{"index": 0, "message": message, "finish_reason": finish}],
            }
            body = json.dumps(response).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        state = {}
        answer = reply(
            "My attendance?",
            {"id": "S001", "role": "student"},
            state,
            api_key="local-test-only",
            provider="groq",
            base_url=f"http://127.0.0.1:{server.server_port}/v1",
        )
        assert answer == "Attendance checked successfully."
        assert len(requests) == 2
        assert requests[0]["model"] == GROQ_MODEL
        assert len(requests[0]["tools"]) == 6
        assert any(message["role"] == "tool" for message in requests[1]["messages"])
        assert len(state["trace"][0]["result"]["courses"]) == 4
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


@pytest.mark.parametrize(
    "status,phrase",
    [(402, "credits"), (401, "token"), (403, "permissions"), (429, "rate limit")],
)
def test_provider_errors_are_actionable(status, phrase):
    from campusbuddy.model import model_error_message

    error = RuntimeError("private provider failure")
    error.status_code = status
    answer = model_error_message(error)
    assert phrase in answer.lower()
    assert "private provider failure" not in answer
