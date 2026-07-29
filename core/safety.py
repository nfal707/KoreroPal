CRISIS_KEYWORDS = [
    "suicide",
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
    text = message.lower()

    if any(keyword in text for keyword in CRISIS_KEYWORDS):
        return "crisis"

    if any(keyword in text for keyword in HIGH_DISTRESS_KEYWORDS):
        return "high"

    return "normal"


def crisis_response():
    return (
        "I'm really sorry you're feeling this way. KōreroPal is not a crisis service, "
        "but you deserve real support now.\n\n"
        "If you are in immediate danger in New Zealand, call 111 now.\n\n"
        "You can also call or text 1737 anytime to speak with a trained counsellor. "
        "Lifeline NZ is available on 0800 543 354 or by texting HELP to 4357.\n\n"
        "If possible, move near another person, contact someone you trust, or go to a safe public place."
    )


def safety_footer():
    return (
        "\n\nReminder: KōreroPal is a wellbeing reflection tool, not a therapist, doctor, "
        "or crisis service."
    )
