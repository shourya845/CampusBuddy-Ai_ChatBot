import streamlit as st

from campusbuddy.database import initialize
from campusbuddy.permissions import directory
from campusbuddy.ui import (
    render_chat,
    render_confirmation,
    render_login,
    render_records,
    render_sidebar,
    render_structured_tools,
    render_tool_evidence,
)

st.set_page_config(page_title="CampusBuddy | T5", page_icon="🎓", layout="wide")
try:
    initialize()
except Exception:
    st.error(
        "Database could not be opened. Check CAMPUSBUDDY_DB and folder permissions."
    )
    st.stop()
if "actor" not in st.session_state:
    render_login()
    st.stop()
actor = st.session_state.actor
state = st.session_state.chat
try:
    directory_data = directory(actor)
except Exception:
    st.error("Your course records are temporarily unavailable. Please retry.")
    st.stop()
st.title(f"Welcome, {actor['name'].split()[0]}")
st.caption("CampusBuddy · Your attendance and academic progress, together.")
provider, api_key, base_url = render_sidebar(actor, state, directory_data)
chat_tab, records_tab, tools_tab = st.tabs(
    ["Assistant", "My records", "Attendance & marks"]
)
with chat_tab:
    render_chat(actor, state, provider, api_key, base_url)
with records_tab:
    render_records(actor, directory_data)
with tools_tab:
    render_structured_tools(actor, state, directory_data)
render_confirmation(actor, state)
render_tool_evidence(state)
