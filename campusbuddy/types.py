from typing import Any, Literal, TypedDict


class Actor(TypedDict):
    id: str
    name: str
    role: Literal["student", "teacher"]


class AgentSession(TypedDict):
    history: list[dict[str, Any]]
    trace: list[dict[str, Any]]
    pending: dict[str, Any] | None
