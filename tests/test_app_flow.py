from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import core.ai as ai
import core.database as database
import core.reflection as reflection


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "ratings.db")
    monkeypatch.setattr(database, "get_secret", lambda name, default=None: default)
    monkeypatch.setattr(ai, "get_secret", lambda name, default=None: default)
    return AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=15).run()


def button(app, label):
    return next(item for item in app.button if item.label == label)


def start_chat(app):
    button(app, "Start a reflection").click().run()
    app.checkbox[0].check()
    button(app, "Start reflection").click().run()
    assert not app.exception
    return app


def test_chat_only_shows_ratings_after_end_and_saves_once(app, monkeypatch):
    calls = []
    def reply(*args):
        calls.append(args)
        return "What feels most important about that?", "normal"
    monkeypatch.setattr(reflection, "generate_support_response", reply)
    start_chat(app)
    assert len(app.slider) == 0
    app.chat_input[0].set_value("An exam is worrying me").run()
    assert not app.exception
    assert len(calls) == 1
    assert len(app.slider) == 0
    app.run()
    assert len(calls) == 1
    button(app, "End chat").click().run()
    assert len(app.slider) == 6
    assert not app.chat_input
    app.slider[0].set_value(6)
    button(app, "Save and see my reflection").click().run()
    assert not app.exception
    assert len(app.metric) == 3
    code = app.session_state.anonymous_id
    assert len(database.load_evaluation_sessions(code)) == 1
    assert app.session_state.chat["history"] == []
    app.run()
    assert len(database.load_evaluation_sessions(code)) == 1


def test_end_chat_command_does_not_call_ai(app, monkeypatch):
    monkeypatch.setattr(reflection, "generate_support_response", lambda *args: pytest.fail("Unexpected API call"))
    start_chat(app)
    app.chat_input[0].set_value("end chat").run()
    assert not app.exception
    assert len(app.slider) == 6
    button(app, "Return to chat").click().run()
    assert len(app.slider) == 0
    assert app.chat_input


def test_creator_questions_stay_correct_through_chat(app, monkeypatch):
    monkeypatch.setattr(ai, "groq_available", lambda: True)
    monkeypatch.setattr(ai, "call_groq", lambda *args: pytest.fail("Creator question reached provider"))
    start_chat(app)
    for message in ["who created koreropal", "a small group of students?", "not just one student?"]:
        app.chat_input[0].set_value(message).run()
        assert not app.exception
        answer = app.session_state.chat["history"][-1]
        assert answer["role"] == "assistant"
        assert "Nick Falkov" in answer["content"]
        assert "built by one student" in answer["content"]
        assert not app.slider


def test_consent_and_legacy_link(app):
    button(app, "Start a reflection").click().run()
    button(app, "Start reflection").click().run()
    assert not app.chat_input
    assert app.warning
    assert "study" not in app.query_params


def test_identity_switch_clears_private_session_data(app):
    start_chat(app)
    app.chat_input[0].set_value("A private thought").run()
    old_code = app.session_state.anonymous_id
    button(app, "Start with a new code").click().run()
    assert not app.exception
    assert app.session_state.anonymous_id != old_code
    assert app.session_state.chat["history"] == []
    assert app.session_state.before_ratings is None


def test_failed_save_keeps_ratings_for_retry(app, monkeypatch):
    start_chat(app)
    button(app, "End chat").click().run()
    original = database.save_evaluation_session
    def fail(*args):
        raise database.DatabaseConnectionError("The database took too long to respond.")
    monkeypatch.setattr(database, "save_evaluation_session", fail)
    app.slider[0].set_value(6)
    button(app, "Save and see my reflection").click().run()
    assert app.error
    assert app.session_state.chat_phase == "after"
    assert app.slider[0].value == 6
    monkeypatch.setattr(database, "save_evaluation_session", original)
    button(app, "Save and see my reflection").click().run()
    assert not app.exception
    assert app.session_state.chat_phase == "complete"


def test_crisis_does_not_wait_for_database(app, monkeypatch):
    start_chat(app)
    monkeypatch.setattr(database, "load_daily_checkins", lambda *args: pytest.fail("Crisis waited for database"))
    app.chat_input[0].set_value("I can’t go on").run()
    assert not app.exception
    assert app.session_state.chat["history"][-1]["risk"] == "crisis"


def test_legacy_url_code_is_loaded_then_removed(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "ratings.db")
    monkeypatch.setattr(database, "get_secret", lambda name, default=None: default)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=15)
    app.query_params["study"] = "KP-ABCDEFGHIJ"
    app.run()
    assert not app.exception
    assert app.session_state.anonymous_id == "KP-ABCDEFGHIJ"
    assert "study" not in app.query_params
