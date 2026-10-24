from datetime import datetime
from zoneinfo import ZoneInfo


RESOURCE_TOPICS = ["All topics", "Stress", "Anxiety", "Low mood", "Sleep", "Mindfulness", "Student life"]

RESOURCES = [
    {
        "id": "just-a-thought-courses",
        "title": "Just a Thought courses",
        "provider": "Just a Thought",
        "summary": "Free online courses covering anxiety, low mood, stress and sleep. Read the course "
        "information to decide whether it suits you.",
        "topics": ["Stress", "Anxiety", "Low mood", "Sleep", "Mindfulness"],
        "format": "Online courses",
        "access": "Free · Account required for courses",
        "url": "https://www.justathought.co.nz/courses",
    },
    {
        "id": "wellbeing-space",
        "title": "The Wellbeing Space",
        "provider": "Just a Thought",
        "summary": "Browse worksheets, videos and reading on worries, stress, sleep and wellbeing. Useful if"
        " you want a specific resource rather than a full course.",
        "topics": ["Stress", "Anxiety", "Low mood", "Sleep", "Mindfulness"],
        "format": "Resource library",
        "access": "Free · Browse without signing in",
        "url": "https://www.justathought.co.nz/the-wellbeing-space",
    },
    {
        "id": "depression-nz",
        "title": "Depression.org.nz",
        "provider": "Health New Zealand | Te Whatu Ora",
        "summary": "Information about depression and anxiety, people's experiences, and options for seeking "
        "support for yourself or someone you know.",
        "topics": ["Low mood", "Anxiety"],
        "format": "Information and support",
        "access": "Public information · No account needed",
        "url": "https://www.depression.org.nz/",
    },
    {
        "id": "coping-with-stress",
        "title": "Coping with Stress",
        "provider": "Just a Thought",
        "summary": "A structured course about understanding stress and learning practical ways to respond to"
        " it. Work through the lessons at your own pace.",
        "topics": ["Stress", "Student life"],
        "format": "Online course",
        "access": "Free · Account required for the course",
        "url": "https://www.justathought.co.nz/courses/coping-with-stress",
    },
    {
        "id": "managing-insomnia",
        "title": "Managing Insomnia",
        "provider": "Just a Thought",
        "summary": "A course about ongoing sleep difficulties, including thoughts and habits that affect "
        "sleep. Read the provider's overview before starting.",
        "topics": ["Sleep"],
        "format": "Online course",
        "access": "Free · Account required for the course",
        "url": "https://www.justathought.co.nz/courses/managing-insomnia",
    },
    {
        "id": "rangatahi",
        "title": "Mental health for rangatahi",
        "provider": "Depression.org.nz",
        "summary": "Information for young people, with links to understanding mental health and finding "
        "support in Aotearoa.",
        "topics": ["Student life", "Low mood", "Anxiety"],
        "format": "Youth information",
        "access": "Public information · No account needed",
        "url": "https://www.depression.org.nz/life-experiences/rangatahi",
    },
]

# Keep old bookmarks working after replacing the written guides.
LEGACY_GUIDE_PATHS = [
    "when-everything-feels-urgent", "a-gentler-way-to-pause", "make-room-for-rest",
    "movement-that-meets-you-here", "food-with-a-little-less-pressure", "small-steps-towards-what-matters",
]

PROMPTS = [
    "What is one thing you need a little more of today?",
    "What felt lighter than you expected?",
    "What is taking up space in your mind, and what can wait?",
    "Who helps you feel like yourself?",
    "What is one small thing you want to carry into tomorrow?",
    "What did you notice when you slowed down?",
    "What would a kind, realistic next step look like?",
]


def local_day():
    return datetime.now(ZoneInfo("Pacific/Auckland")).date()


def daily_prompt(offset=0):
    return PROMPTS[(local_day().toordinal() + offset) % len(PROMPTS)]


def filter_resources(query="", topic="All topics"):
    query = query.strip().casefold()
    return [
        resource for resource in RESOURCES
        if (topic == "All topics" or topic in resource["topics"])
        and query in " ".join([resource["title"], resource["provider"], resource["summary"], *resource["topics"]]).casefold()
    ]
