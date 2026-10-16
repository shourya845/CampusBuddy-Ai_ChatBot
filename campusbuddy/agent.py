import re

from .confirmation import confirm
from .demo import demo_route
from .permissions import privacy_refusal
from .presentation import render
from .settings import DEFAULT_PROVIDER
from .tool_registry import safe_execute
from .types import Actor, AgentSession


def remember(state, text, answer):
    state["history"].extend(
        [{"role": "user", "content": text}, {"role": "assistant", "content": answer}]
    )
    return answer


def missing_attendance_date(text):
    request = text.lower()
    if "mark attendance" not in request:
        return False
    date_pattern = r"\b(?:today|yesterday|tomorrow|same date|that date|last class|monday|tuesday|wednesday|thursday|friday|saturday|sunday|january|february|march|april|may|june|july|august|september|october|november|december)\b|\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?\b"
    return re.search(date_pattern, request) is None


def reply(
    text: str,
    actor: Actor,
    state: AgentSession,
    api_key: str | None = None,
    provider: str | None = None,
    base_url: str | None = None,
) -> str:
    state.setdefault("history", [])
    state.setdefault("pending", None)
    state.setdefault("trace", [])
    if (
        text.strip().lower() in ("cancel", "cancel it", "no", "reject")
        and state["pending"]
    ):
        try:
            result = confirm(actor, state["pending"]["proposal_id"], False)
            answer = render(result)
        except (ValueError, PermissionError) as error:
            answer = str(error)
        state["pending"] = None
        return remember(state, text, answer)
    if missing_attendance_date(text):
        return remember(state, text, "What class date (YYYY-MM-DD) should I use?")

    refusal = privacy_refusal(text, actor)
    if refusal:
        return remember(state, text, refusal)
    selected_provider = provider or ("demo" if api_key == "" else DEFAULT_PROVIDER)
    if selected_provider != "demo":
        from .model import run_agent

        return run_agent(text, actor, state, api_key, selected_provider, base_url)
    (name, arguments, answer) = demo_route(text, actor, state)
    if name:
        result = safe_execute(actor, name, arguments)
        state["trace"].append({"tool": name, "arguments": arguments, "result": result})
        if result.get("status") == "confirmation_required":
            state["pending"] = result
        answer = render(result)
    return remember(state, text, answer)
