import streamlit as st

from campusbuddy.database import initialize
from campusbuddy.permissions import directory
from campusbuddy.ui import (
    render_chat,
    render_dashboard,
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
provider, api_key, base_url = render_sidebar(actor, state, directory_data)
st.html("""
<style>
[data-testid="stAppViewContainer"] {background: #FF9568;}
[data-testid="stHeader"] {background: transparent;}
[data-testid="stMain"] {background: #FFFFFF; border: 12px solid #FF9568; border-radius: 20px;}
[data-testid="stMainBlockContainer"] {background: #FFFFFF; border-radius: 20px;
    margin: 0 auto; padding: 28px 24px; max-width: 1500px; min-height: 88vh;}
[data-testid="stSidebar"] {background: #FFFFFF; border-right: 1px solid #EDF0F2;}
[data-testid="stMetric"] {background: #FFFFFF; border-radius: 10px;}
[data-testid="stMetricLabel"] {color: #6D747C; font-size: .85rem;}
[data-testid="stMetricValue"] {font-size: 1.8rem; font-weight: 600;}
[data-testid="stSidebar"] [role="radiogroup"] label {padding: 8px 10px; border-radius: 6px;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {background: #F0F2F4;}
h1 {font-size: 1.7rem !important; letter-spacing: -.03em;}
h3 {font-size: 1.05rem !important;}
@media (max-width: 700px) {
    [data-testid="stMainBlockContainer"] {margin: 8px auto; padding: 20px 16px;}
}
</style>
""")
page = st.session_state.navigation
heading, profile = st.columns([3, 1])
heading.title(page)
profile.caption(f"{actor['name']} · {actor['role'].title()}")
st.divider()
if page == "Dashboard":
    render_dashboard(actor, directory_data)
elif page == "Assistant":
    render_chat(actor, state, provider, api_key, base_url)
elif page == "My records":
    render_records(actor, directory_data)
else:
    render_structured_tools(actor, state, directory_data)
render_confirmation(actor, state)
if page == "Assistant":
    render_tool_evidence(state)
