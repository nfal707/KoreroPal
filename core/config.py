import os
from pathlib import Path



APP_NAME = "KōreroPal"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
LIKERT_MIN = 1
LIKERT_MAX = 7

NZ_RESOURCES = [
    {
        "name": "Emergency",
        "contact": "Call 111",
        "when": "Immediate danger or urgent medical emergency",
    },
    {
        "name": "1737",
        "contact": "Call or text 1737",
        "when": "Free support from a trained counsellor in New Zealand",
    },
    {
        "name": "Lifeline NZ",
        "contact": "0800 543 354 or text HELP to 4357",
        "when": "Emotional distress or crisis support",
    },
    {
        "name": "Youthline",
        "contact": "0800 376 633 or text 234",
        "when": "Support for young people",
    },
    {
        "name": "Healthline",
        "contact": "0800 611 116",
        "when": "General health advice",
    },
]


def get_secret(name, default=None):
    value = os.getenv(name)

    if value:
        return value

    project_secrets = (
        Path(__file__).resolve().parent.parent / ".streamlit" / "secrets.toml"
    )
    user_secrets = Path.home() / ".streamlit" / "secrets.toml"

    if project_secrets.exists() or user_secrets.exists():
        try:
            import streamlit as st

            value = st.secrets.get(name)
        except Exception:
            value = None
    else:
        value = None

    if value:
        return value

    return default
