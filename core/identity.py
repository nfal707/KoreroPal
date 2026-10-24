import re
import secrets


def create_anonymous_id():
    return f"KP-{secrets.token_hex(20).upper()}"


def valid_anonymous_id(value):
    if not isinstance(value, str):
        return False

    return bool(re.fullmatch(r"KP-(?:[A-Z0-9]{10}|[A-F0-9]{40})", value))


def validate_anonymous_id(value):
    if not valid_anonymous_id(value):
        raise ValueError("A valid private recovery code is required.")
