import os
import time

import streamlit as st

from .agent import reply
from .confirmation import confirm
from .database import authenticate
from .presentation import render
from .settings import (
    DEFAULT_PROVIDER,
    GROQ_MODEL,
    INTRO,
    today,
)
from .tool_registry import safe_execute


def render_login():
    st.html("""
    <style>
    [data-testid="stAppViewContainer"] {background: #e4f5f8;}
    [data-testid="stHeader"] {background: transparent;}
    .st-key-login_shell {max-width: 420px; margin: 5vh auto 2rem; padding: 32px 28px;
        background: rgba(255,255,255,.88); border: 1px solid #bee0e7;
        border-radius: 28px; box-shadow: 0 12px 36px #488a9c20, 0 3px 5px #488a9c12;}
    .st-key-login_shell h1 {text-align: center; font-size: 1.6rem; letter-spacing: -.04em;}
    .st-key-login_shell [data-testid="stForm"] {border: 0; padding: 0;}
    .st-key-login_shell [data-testid="stFormSubmitButton"] button {
        background: #27272e; color: white; border: 0; border-radius: 12px; min-height: 44px;}
    .st-key-login_shell [data-testid="stFormSubmitButton"] button:hover {background: #404049;}
    .login-icon {width: 54px; height: 54px; margin: 0 auto 18px; display: grid;
        place-items: center; background: #effbfd; border-radius: 17px;
        box-shadow: 0 5px 12px #53879820; font-size: 26px; color: #34464c;}
    .login-subtitle {text-align: center; color: #68767e; line-height: 1.6; margin-bottom: 20px;}
    .login-footer {text-align: center; color: #68767e; font-size: .8rem; margin-top: 12px;}
    @media (max-width: 600px) {.st-key-login_shell {margin-top: 1rem; padding: 24px 20px;}}
    </style>
    """)
    with st.container(key="login_shell"):
        st.html('<div class="login-icon" aria-hidden="true">↪</div>')
        st.title("Welcome to CampusBuddy")
        st.html('<p class="login-subtitle">Your attendance. Your progress. One place.<br>Sign in to your campus account.</p>')
        render_login_form()
        with st.expander("Try a demo account"):
            st.write("Teacher: **T001** · Student: **S001**")
            st.write("Password: **Campus@123**")
            st.caption("Teachers T001–T025 · Students S001–S200")
        st.html('<p class="login-footer">T5 · Attendance & Academic Progress Assistant</p>')
    st.stop()


def render_login_form():
    with st.form("login", border=False):
        user_id = st.text_input("User ID", placeholder="Enter your student or teacher ID").strip().upper()
        password_text = st.text_input("Password", type="password", placeholder="Enter your password")
        submitted = st.form_submit_button("Sign in", type="primary", width="stretch")
    if submitted:
        attempts = st.session_state.setdefault("attempts", [])
        now = time.time()
        attempts[:] = [t for t in attempts if now - t < 60]
        if len(attempts) >= 5:
            st.error("Please wait a minute before trying again.")
        else:
            attempts.append(now)
            try:
                actor = authenticate(user_id, password_text)
            except Exception:
                st.error("Sign-in is temporarily unavailable. Please retry.")
                return
            if actor:
                st.session_state.actor = actor
                st.session_state.chat = {"history": [], "pending": None, "trace": []}
                st.rerun()
            else:
                st.error("Incorrect user ID or password.")



def render_records(actor, directory_data):
    if actor["role"] == "student":
        result = safe_execute(actor, "get_report_card", {})
        if "error" in result:
            st.error(result["error"])
        else:
            for record in result["courses"]:
                with st.container(border=True):
                    st.subheader(record["course"])
                    columns = st.columns(3)
                    columns[0].metric(
                        "Attendance",
                        f"{record['percentage']}%"
                        if record["percentage"] is not None
                        else "No classes",
                    )
                    columns[1].metric(
                        "Marks",
                        f"{record['weighted_percentage']}%"
                        if record["weighted_percentage"] is not None
                        else "Pending",
                    )
                    columns[2].metric("Grade", record["grade"])
                    st.write(record["message"])
                    st.dataframe(record["exams"], hide_index=True)
    else:
        st.caption("Only students enrolled in your assigned courses are shown.")
        st.dataframe(directory_data["students"], hide_index=True)
        for course in directory_data["courses"]:
            result = safe_execute(
                actor, "list_shortage_students", {"course_id": course["course_id"]}
            )
            st.subheader(course["name"])
            if "error" in result:
                st.error(result["error"])
                continue
            st.write(f"{result.get('count', 0)} students below 75%")
            st.dataframe(result.get("below_75", []), hide_index=True)


def render_structured_tools(actor, state, directory_data):
    st.subheader("Attendance & marks")
    st.caption("Choose an action below. Changes are saved only after your confirmation.")
    course = st.selectbox(
        "Course", directory_data["courses"], format_func=lambda c: c["name"]
    )
    if course:
        if actor["role"] == "teacher":
            operation = st.selectbox(
                "Action",
                [
                    "Bulk attendance",
                    "Enter marks",
                    "Attendance",
                    "Classes needed",
                    "Report card",
                    "Shortage list",
                ],
            )
            roster = directory_data["students"]
            selected = st.selectbox(
                "Student (for individual actions)",
                roster,
                format_func=lambda s: (
                    f"Roll {s['roll_no']} · {s['name']} · {s['student_id']}"
                ),
            )
            student_id = selected["student_id"] if selected else None
        else:
            operation = st.selectbox(
                "Action", ["Attendance", "Classes needed", "Report card"]
            )
            student_id = actor["id"]
        day = (
            st.date_input("Class date", value=today(), max_value=today())
            if operation == "Bulk attendance"
            else None
        )
        absent = (
            st.text_input("Absent roll numbers, comma separated (empty = all present)")
            if operation == "Bulk attendance"
            else ""
        )
        if operation == "Enter marks":
            exam = st.selectbox("Exam", ["MID", "FINAL"])
            maximum = 50 if exam == "MID" else 100
            score = st.number_input(
                f"Score out of {maximum}",
                min_value=0.0,
                max_value=float(maximum),
                step=1.0,
            )
        target = (
            st.number_input("Target %", min_value=1.0, max_value=100.0, value=75.0)
            if operation == "Classes needed"
            else 75
        )
        if st.button(
            "Prepare change"
            if operation in ("Bulk attendance", "Enter marks")
            else "Get result",
            type="primary",
        ):
            try:
                if operation == "Bulk attendance":
                    (tool_name, arguments) = (
                        "mark_attendance",
                        {
                            "course_id": course["course_id"],
                            "class_date": day.isoformat(),
                            "absent_rolls": [
                                int(x.strip()) for x in absent.split(",") if x.strip()
                            ],
                        },
                    )
                elif operation == "Enter marks":
                    (tool_name, arguments) = (
                        "add_marks",
                        {
                            "student_id": student_id,
                            "course_id": course["course_id"],
                            "exam_type": exam,
                            "score": score,
                            "max_score": maximum,
                        },
                    )
                elif operation == "Shortage list":
                    (tool_name, arguments) = (
                        "list_shortage_students",
                        {"course_id": course["course_id"]},
                    )
                elif operation == "Report card":
                    (tool_name, arguments) = (
                        "get_report_card",
                        {"student_id": student_id},
                    )
                else:
                    (tool_name, arguments) = (
                        "classes_needed_for_target"
                        if operation == "Classes needed"
                        else "get_attendance_percentage",
                        {"student_id": student_id, "course_id": course["course_id"]},
                    )
                if operation == "Classes needed":
                    arguments["target"] = target
                result = safe_execute(actor, tool_name, arguments)
                if result.get("status") == "confirmation_required":
                    state["pending"] = result
                st.session_state.last_result = result
            except ValueError:
                st.error("Please enter valid comma-separated roll numbers.")
        if st.session_state.get("last_result"):
            st.write(render(st.session_state.last_result))


def render_confirmation(actor, state):
    if state.get("pending"):
        with st.container(border=True):
            st.subheader("Review change before saving")
            st.json(state["pending"]["proposed_change"])
            if state["pending"].get("total_students"):
                st.write(
                    f"{state['pending']['present']} present · {state['pending']['absent']} absent · {state['pending']['total_students']} total"
                )
            st.caption(
                "This will insert or update the shown records. Nothing is saved until you confirm."
            )
            (yes, no) = st.columns(2)
            decision = (
                True
                if yes.button("Confirm change", type="primary")
                else False
                if no.button("Cancel change")
                else None
            )
            if decision is not None:
                try:
                    result = confirm(actor, state["pending"]["proposal_id"], decision)
                    state["history"].append(
                        {"role": "assistant", "content": render(result)}
                    )
                    st.session_state.last_result = result
                except Exception as e:
                    state["history"].append(
                        {"role": "assistant", "content": "Change not saved: " + str(e)}
                    )
                state["pending"] = None
                st.rerun()


def render_sidebar(actor, state, directory_data):
    modes = {"Groq API": "groq", "Offline demo": "demo"}
    default_provider = os.getenv("MODEL_PROVIDER", DEFAULT_PROVIDER)
    default_index = (
        list(modes.values()).index(default_provider)
        if default_provider in modes.values()
        else 0
    )
    api_key = ""
    base_url = None
    with st.sidebar:
        st.markdown("### CampusBuddy")
        st.caption("YOUR CAMPUS COMPANION")
        st.divider()
        st.subheader(actor["name"])
        st.caption(f"{actor['id']} · {actor['role'].title()}")
        selected_mode = st.radio("Assistant mode", list(modes), index=default_index)
        provider = modes[selected_mode]
        if provider == "groq":
            api_key = st.text_input(
                "Groq API key (optional if in .env)",
                type="password",
                value=os.getenv("GROQ_API_KEY", ""),
            )
            st.caption(GROQ_MODEL)
            if not api_key:
                st.warning("Enter your Groq key or choose Offline demo.")
        else:
            st.caption("Deterministic demo; no LLM calls")
        st.write("Your courses")
        for course in directory_data["courses"]:
            st.caption(f"{course['course_id']} · {course['name']}")
        if st.button("Clear conversation"):
            state["history"] = []
            state["trace"] = []
            st.rerun()
        if st.button("Sign out"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    return (provider, api_key, base_url)


def render_chat(actor, state, provider, api_key, base_url):
    if not state["history"]:
        st.info(INTRO)
    for message in state["history"]:
        if message["role"] in ("user", "assistant") and message.get("content"):
            with st.chat_message(message["role"]):
                st.write(message["content"])
    text = st.chat_input("Ask CampusBuddy…", submit_mode="disable")
    if not text:
        return
    if provider != "demo" and (not api_key):
        st.error(
            "Enter the selected provider API key in the sidebar or choose Offline demo."
        )
        return
    with st.spinner("CampusBuddy is checking…"):
        try:
            reply(
                text,
                actor,
                state,
                api_key=api_key,
                provider=provider,
                base_url=base_url,
            )
        except Exception:
            state["history"].append(
                {
                    "role": "assistant",
                    "content": "I could not complete that request. Please check the details and retry.",
                }
            )
    st.rerun()


def render_tool_evidence(state):
    with st.expander("Tool execution evidence"):
        st.caption("Database tool results for this session. No API key is shown.")
        for trace in state["trace"][-12:]:
            st.json(trace)
