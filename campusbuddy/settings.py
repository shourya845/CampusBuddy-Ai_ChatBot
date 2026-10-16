import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
SCHEMA_PATH = ROOT / "database" / "schema.sql"
PROMPT_PATH = ROOT / "campusbuddy" / "system_prompt.txt"
GROQ_MODEL = "openai/gpt-oss-20b"
DEFAULT_PROVIDER = os.getenv("MODEL_PROVIDER", "groq")
ATTENDANCE_TARGET = 75
PROPOSAL_EXPIRY_SECONDS = 600
HISTORY_LIMIT = 80
AGENT_RECURSION_LIMIT = 14
GRADE_BOUNDARIES = [
    (90, "A+"),
    (80, "A"),
    (70, "B"),
    (60, "C"),
    (50, "D"),
    (40, "E"),
    (0, "F"),
]
INTRO = "I'm CampusBuddy, your Attendance & Academic Progress Assistant. Ask me about attendance, marks, or reaching 75%. Teachers can propose attendance and marks changes for confirmation."


def today():
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()
