STRATEGIES = {
    "stress": {
        "title": "Stress reset",
        "steps": [
            "Take five slow breaths.",
            "Write down the one thing that needs doing first.",
            "Set a 10 minute timer and do only the first step.",
        ],
    },
    "anxiety": {
        "title": "Grounding exercise",
        "steps": [
            "Name 5 things you can see.",
            "Name 4 things you can feel.",
            "Name 3 things you can hear.",
            "Name 2 things you can smell.",
            "Name 1 thing you can taste.",
        ],
    },
    "study": {
        "title": "Study restart",
        "steps": [
            "Pick one small question.",
            "Work for 25 minutes.",
            "Afterwards, write one mistake and one fix.",
        ],
    },
    "sleep": {
        "title": "Wind-down checklist",
        "steps": [
            "Dim your screen.",
            "Put your phone away for 15 minutes.",
            "Write tomorrow's first task on paper.",
        ],
    },
    "low mood": {
        "title": "Tiny action plan",
        "steps": [
            "Drink water.",
            "Step outside or open a window.",
            "Message one person or complete one small task.",
        ],
    },
    "anger": {
        "title": "Cool-down plan",
        "steps": [
            "Step away from the trigger for 2 minutes.",
            "Unclench your jaw and lower your shoulders.",
            "Write the message you want to send, but do not send it yet.",
        ],
    },
}


def choose_strategy(message):
    text = message.lower()

    if any(w in text for w in ["stress", "stressed", "overwhelmed", "pressure", "too much"]):
        return "stress", STRATEGIES["stress"]
    if any(w in text for w in ["anxious", "anxiety", "panic", "worried", "scared"]):
        return "anxiety", STRATEGIES["anxiety"]
    if any(w in text for w in ["study", "exam", "test", "assignment", "focus", "uni"]):
        return "study", STRATEGIES["study"]
    if any(w in text for w in ["sleep", "tired", "exhausted", "insomnia"]):
        return "sleep", STRATEGIES["sleep"]
    if any(w in text for w in ["sad", "down", "low", "unmotivated", "empty"]):
        return "low mood", STRATEGIES["low mood"]
    if any(w in text for w in ["angry", "rage", "furious", "annoyed"]):
        return "anger", STRATEGIES["anger"]

    return "general", {
        "title": "Small reset",
        "steps": [
            "Pause for a moment.",
            "Name what you are feeling in one sentence.",
            "Choose one tiny next action.",
        ],
    }


def format_strategy(strategy):
    lines = [f"Try this: {strategy['title']}"]
    for step in strategy["steps"]:
        lines.append(f"- {step}")
    return "\n".join(lines)
