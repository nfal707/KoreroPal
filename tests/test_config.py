from core.config import APP_NAME, DEFAULT_GROQ_MODEL


def test_app_name():
    assert APP_NAME == "KōreroPal"


def test_default_groq_model():
    assert DEFAULT_GROQ_MODEL == "llama-3.3-70b-versatile"
