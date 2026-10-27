import threading
import time

from core.ai import generate_support_response
from core.config import MAX_CHAT_TURNS, MAX_MESSAGE_LENGTH
from core.safety import assess_risk, crisis_response


def create_chat():
    return {
        "history": [],
        "requests": set(),
        "busy": False,
        "last_sent": None,
        "lock": threading.Lock(),
    }


def is_end_chat(message):
    return message.strip().lower().rstrip(".!?") in {"end chat", "end the chat"}


def send_message(chat, request_id, message, recent_context=""):
    """Handle each submitted turn once, including during a Streamlit rerun."""

    message = message.strip()

    if not message or len(message) > MAX_MESSAGE_LENGTH:
        raise ValueError(f"Please write between 1 and {MAX_MESSAGE_LENGTH} characters.")

    risk = assess_risk(message)

    with chat["lock"]:
        if request_id in chat["requests"] or chat["busy"]:
            return False

        if risk != "crisis":
            if len(chat["history"]) // 2 >= MAX_CHAT_TURNS:
                raise ValueError("This reflection is full. End chat to review how you feel.")

            if chat["last_sent"] is not None and time.monotonic() - chat["last_sent"] < 3:
                raise ValueError("Please take a moment before sending another message.")

        chat["requests"].add(request_id)
        chat["busy"] = True
        chat["last_sent"] = time.monotonic()
        history = chat["history"][-30:].copy()
        chat["history"].append({"role": "user", "content": message})

    response = "That reply was interrupted. Please send a new message when you're ready."
    try:
        response, risk = generate_support_response(message, recent_context, history)
    except Exception:
        response = crisis_response() if risk == "crisis" else (
            "I couldn't finish that reply. You can try a new message, take a break, "
            "or open the coping toolkit."
        )
    finally:
        with chat["lock"]:
            # Interrupted requests are not automatically sent to the provider again.
            chat["history"].append({"role": "assistant", "content": response, "risk": risk})
            chat["busy"] = False

    return True
