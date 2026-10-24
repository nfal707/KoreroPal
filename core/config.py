import os
from pathlib import Path



APP_NAME = "KōreroPal"
DEFAULT_GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_MESSAGE_LENGTH = 2000
MAX_CHAT_TURNS = 30
SAFETY_NOTICE = (
    "KōreroPal is a wellbeing reflection tool, not a therapist, doctor, or crisis service."
)
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
        "contact": "Call [1737](tel:1737?oai_link_source=model_response_hotline) or text [1737](sms:1737?oai_link_source=model_response_hotline)",
        "when": "Free support from a trained counsellor in New Zealand",
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
