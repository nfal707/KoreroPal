import re
import unicodedata


DENIALS = (
    r"\b(?:i(?: am|'m) not|i(?: do not| don't) feel) suicidal\b",
    r"\b(?:i(?: do not| don't) want to die|i want to live)\b",
    r"\b(?:i(?: am|'m) not thinking about (?:suicide|hurting myself|self harm))\b",
    r"\b(?:i would never|i(?: do not| don't) want to) (?:hurt|kill) myself\b",
)

CRISIS_PATTERNS = (
    r"\b(?:suicidal|suicide|self harm|self harming|self injury)\b",
    r"\b(?:kill|hurt|harm|cut|injure) myself\b",
    r"\b(?:kill|hurt|harm) someone\b",
    r"\b(?:overdos(?:e|ed|ing)|took too many pills)\b",
    r"\b(?:end my life|end it all|take my own life|take my life)\b",
    r"\b(?:i |i'?d |i would )?(?:want|wish|hope|prefer|need) to die\b",
    r"\b(?:i wish i (?:was|were) dead|i would rather be dead|better off (?:if i was|without me))\b",
    r"\b(?:i (?:do not|don't) want to wake up|i hope i (?:do not|don't) wake up)\b",
    r"\b(?:i (?:cannot|can't|cant) go on|life (?:is not|isn't) worth living)\b",
    r"\b(?:thinking about|planning|going to|about to) (?:killing myself|ending my life|suicide)\b",
)
HIGH_DISTRESS_PATTERNS = (
    r"\b(?:hopeless|worthless|panicking|panic attack|breakdown|overwhelmed)\b",
    r"\b(?:cannot|can't|cant) cope\b",
    r"\b(?:spiralling|spiraling|falling apart|nothing matters)\b",
)


def _normalise(message):
    if not isinstance(message, str):
        return ""
    text = unicodedata.normalize("NFKC", message).lower()
    text = text.translate(str.maketrans({"’": "'", "‘": "'", "‐": "-", "‑": "-", "–": "-", "—": "-"}))
    return " ".join(text.replace("-", " ").split())


def assess_risk(message):
    text = _normalise(message)
    for expression in DENIALS:
        text = re.sub(expression, " ", text)

    if any(re.search(expression, text) for expression in CRISIS_PATTERNS):
        return "crisis"
    if any(re.search(expression, text) for expression in HIGH_DISTRESS_PATTERNS):
        return "high"
    return "normal"


def crisis_response():
    return (
        "I'm concerned for your safety. KōreroPal isn't a crisis service, and you deserve "
        "support from a real person now.\n\n"
        "If you're in immediate danger in New Zealand, call 111.\n\n"
        "For free 24-hour support in New Zealand, call [1737](tel:1737) or "
        "text [1737](sms:1737).\n\n"
        "Outside New Zealand, contact your local emergency or crisis service. "
        "If you can, move near another person or contact someone you trust."
    )
