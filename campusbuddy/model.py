import json
import logging
import os
import re

from langchain.agents import create_agent
from langchain_core.messages import convert_to_openai_messages
from langchain_core.tools import StructuredTool
from langchain_groq import ChatGroq
from langgraph.errors import GraphRecursionError

from .permissions import directory
from .settings import (
    AGENT_RECURSION_LIMIT,
    GROQ_MODEL,
    HISTORY_LIMIT,
    PROMPT_PATH,
    today,
)
from .tool_registry import safe_execute
from .tool_schemas import SCHEMAS

LOGGER = logging.getLogger(__name__)


class ModelConfigurationError(ValueError):
    pass


def connect_model(api_key=None, provider=None, base_url=None):
    if provider not in (None, "groq"):
        raise ModelConfigurationError("Choose Groq API or Offline demo.")
    api_key = api_key or os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise ModelConfigurationError(
            "Add GROQ_API_KEY to your private .env file or enter it in the sidebar."
        )
    return ChatGroq(
        model=GROQ_MODEL,
        api_key=api_key,
        base_url=base_url,
        temperature=0.2,
        max_tokens=int(os.getenv("MODEL_MAX_TOKENS", "4096")),
        timeout=30,
        max_retries=1,
        model_kwargs={"parallel_tool_calls": False},
    )


def model_tool_result(name, result):
    if name == "list_shortage_students" and "below_75" in result:
        return {
            "course": result["course"],
            "count": result["count"],
            "below_75": [
                {
                    key: student[key]
                    for key in ("student_id", "roll_no", "name", "percentage")
                }
                for student in result["below_75"]
            ],
        }
    return result


def model_directory(actor, state):
    authorized = directory(actor)
    if actor["role"] == "student":
        return authorized
    request = " ".join(
        message.get("content", "") or ""
        for message in state.get("history", [])
        if message.get("role") == "user"
    ).lower()
    requested = []
    for student_record in authorized["students"]:
        identifiers = [
            student_record["student_id"].lower(),
            student_record["name"].lower(),
        ]
        named = any(
            re.search(r"\b" + re.escape(identifier) + r"\b", request)
            for identifier in identifiers
        )
        numbered = re.search(
            r"\broll\s*" + str(student_record["roll_no"]) + r"\b", request
        )
        if named or numbered:
            requested.append(student_record)
    return {
        "courses": authorized["courses"],
        "referenced_students": requested,
        "authorized_student_count": len(authorized["students"]),
        "rule": "Ask for a student ID or roll if a name cannot be resolved unambiguously. Bulk attendance covers all enrolled students.",
    }


def make_tool(definition, actor, state):
    function = definition["function"]
    name = function["name"]

    def call_tool(**arguments):
        result = safe_execute(actor, name, arguments)
        state["trace"].append({"tool": name, "arguments": arguments, "result": result})
        if result.get("status") == "confirmation_required":
            state["pending"] = result
        return json.dumps(model_tool_result(name, result))

    return StructuredTool.from_function(
        func=call_tool,
        name=name,
        description=function["description"],
        args_schema=function["parameters"],
    )


def build_agent(actor, state, api_key=None, provider=None, base_url=None):
    model = connect_model(api_key, provider, base_url)
    tools = [make_tool(definition, actor, state) for definition in SCHEMAS]
    context = {
        "authenticated_user": actor,
        "today_IST": today().isoformat(),
        "authorized_directory": model_directory(actor, state),
    }
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=PROMPT_PATH.read_text()
        + "\nServer-provided context: "
        + json.dumps(context),
    )


def trim_history(history, limit=HISTORY_LIMIT):
    while len(history) > limit:
        next_turn = next(
            (
                index
                for index, message in enumerate(history[1:], 1)
                if message["role"] == "user"
            ),
            None,
        )
        if next_turn is None:
            break
        del history[:next_turn]


def model_error_message(error):
    status = getattr(error, "status_code", None)
    if status == 402:
        return "Your hosted-model account has no remaining inference credits. Restore its credits and retry. This request did not save attendance or marks."
    if status in (401, 403):
        return "The hosted model rejected the API token or its permissions. Check your private .env settings or the sidebar key and retry."
    if status == 429:
        return "The hosted model rate limit was reached. Please wait briefly and retry. This request did not save attendance or marks."
    return "The hosted model is unavailable, or this endpoint does not support tool calling. Check the endpoint and API key, retry, or use the structured tools or Offline demo."


def run_agent(text, actor, state, api_key=None, provider=None, base_url=None):
    state.pop("last_model_error", None)
    history = state["history"]
    history.append({"role": "user", "content": text})
    trim_history(history)
    try:
        agent = build_agent(actor, state, api_key, provider, base_url)
        result = agent.invoke(
            {"messages": history}, config={"recursion_limit": AGENT_RECURSION_LIMIT}
        )
        messages = convert_to_openai_messages(result["messages"])
        answer = messages[-1].get("content") or "Please provide the missing details."
        if not isinstance(answer, str):
            answer = "\n".join(
                block.get("text", "") for block in answer if isinstance(block, dict)
            )
        state["history"] = messages
        return answer
    except ModelConfigurationError as error:
        answer = str(error)
    except GraphRecursionError:
        answer = "I reached the tool-step limit. Please narrow the request."
    except Exception as error:
        LOGGER.warning("CampusBuddy model request failed (%s)", type(error).__name__)
        response = getattr(error, "response", None)
        headers = getattr(response, "headers", {})
        state["last_model_error"] = {
            "status_code": getattr(error, "status_code", None),
            "retry_after": headers.get("retry-after"),
        }
        answer = model_error_message(error)
    history.append({"role": "assistant", "content": answer})
    return answer
