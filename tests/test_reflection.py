import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

import core.reflection as reflection
from core.config import MAX_CHAT_TURNS


def test_duplicate_request_and_concurrent_rerun_only_call_once(monkeypatch):
    started = threading.Event()
    finish = threading.Event()
    calls = []

    def reply(*args):
        calls.append(args)
        started.set()
        assert finish.wait(5)
        return "One reply", "normal"

    monkeypatch.setattr(reflection, "generate_support_response", reply)
    chat = reflection.create_chat()
    with ThreadPoolExecutor() as executor:
        pending = executor.submit(reflection.send_message, chat, "turn-1", "I'm stressed")
        assert started.wait(5)
        assert not reflection.send_message(chat, "turn-1", "I'm stressed")
        assert not reflection.send_message(chat, "turn-2", "another message")
        finish.set()
        assert pending.result()

    assert not reflection.send_message(chat, "turn-1", "I'm stressed")
    assert len(calls) == 1
    assert [item["role"] for item in chat["history"]] == ["user", "assistant"]


def test_failure_is_not_retried_and_new_turn_can_continue(monkeypatch):
    def fail(*args):
        raise RuntimeError("private exception")

    monkeypatch.setattr(reflection, "generate_support_response", fail)
    chat = reflection.create_chat()
    reflection.send_message(chat, "turn-1", "A hard day")
    assert not chat["busy"]
    assert "private exception" not in chat["history"][-1]["content"]
    assert not reflection.send_message(chat, "turn-1", "A hard day")
    chat["last_sent"] = None
    assert reflection.send_message(chat, "turn-2", "A hard day")


def test_crisis_bypasses_turn_and_cooldown_limits(monkeypatch):
    monkeypatch.setattr(reflection, "generate_support_response", lambda *args: ("Get real support", "crisis"))
    chat = reflection.create_chat()
    chat["history"] = [{"role": "user", "content": "test"}] * (MAX_CHAT_TURNS * 2)
    assert reflection.send_message(chat, "crisis", "I want to die")
    assert chat["history"][-1]["risk"] == "crisis"
    with pytest.raises(ValueError, match="full"):
        reflection.send_message(chat, "normal", "Hello")


def test_end_chat_is_an_explicit_command():
    assert reflection.is_end_chat(" End chat! ")
    assert reflection.is_end_chat("end the chat")
    assert not reflection.is_end_chat("I want to end chat but I want to die")


def test_message_length_checked_before_call(monkeypatch):
    monkeypatch.setattr(reflection, "generate_support_response", lambda *args: pytest.fail("Unexpected API call"))
    with pytest.raises(ValueError):
        reflection.send_message(reflection.create_chat(), "long", "x" * 2001)
