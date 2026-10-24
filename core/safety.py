import unicodedata


CRISIS_KEYWORDS = [
    "suicide",
    "suicidal",
    "kill myself",
    "overdose",
    "took too many pills",
    "hurt someone",
    "kill someone",
    "kill myself",
    "end my life",
    "end it all",
    "hurt myself",
    "self harm",
    "self-harm",
    "i want to die",
    "want to die",
    "can't go on",
    "cant go on",
    "not worth living",
]

HIGH_DISTRESS_KEYWORDS = [
    "hopeless",
    "worthless",
    "panic",
    "panicking",
    "breakdown",
    "can't cope",
    "cant cope",
    "overwhelmed",
    "spiral",
]


def assess_risk(message):
    text = unicodedata.normalize("NFKC", message).lower()
    text = " ".join(text.replace("’", "'").replace("-", " ").split())

    if any(keyword.replace("-", " ") in text for keyword in CRISIS_KEYWORDS):
        return "crisis"

    if any(keyword in text for keyword in HIGH_DISTRESS_KEYWORDS):
        return "high"

    return "normal"


def crisis_response():
    return (
        "I'm really sorry you're feeling this way. KōreroPal is not a crisis service, "
        "but you deserve real support now.\n\n"
        "If you are in immediate danger in New Zealand, call 111 now.\n\n"
        "You can call [1737](tel:1737?oai_link_source=model_response_hotline) or "
        "text [1737](sms:1737?oai_link_source=model_response_hotline) for free support, 24 hours a day.\n\n"
        "Outside New Zealand, contact your local emergency or crisis service.\n\n"
        "If possible, move near another person, contact someone you trust, or go to a safe public place."
    )
