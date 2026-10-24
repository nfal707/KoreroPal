import re
from html import escape
from urllib.parse import urlencode, urlparse

import streamlit as st

from core.config import get_secret
from core.content import RESOURCES, RESOURCE_TOPICS, daily_prompt, filter_resources, local_day
from core.ui import ROOT, asset_url, go, intro, page_link, section_title


def breathing_timer():
    st.iframe(ROOT / "assets" / "breathing.html", height="content", alt="Interactive breathing timer")


def resource_card(resource, key):
    with st.container(border=True, key=key):
        st.html(f'<div class="resource-label">{escape(resource["format"])}</div>')
        st.subheader(resource["title"])
        st.caption(resource["provider"])
        st.write(resource["summary"])
        st.caption(resource["access"])
        st.link_button(f"Visit {resource['title']} ↗", resource["url"])


def home_page():
    with st.container(key="home_hero"):
        left, right = st.columns([1.2, 1], gap="large", vertical_alignment="center")
        with left:
            st.html(
                '<p class="eyebrow">KŌREROPAL / WELLBEING REFLECTION</p>'
                '<h1 class="hero-title">What’s on your mind?</h1>'
                '<p class="hero-description">Talk through your day, write in your journal, '
                'or check in with how you’re feeling. You choose what to share and when to finish.</p>',
            )
            reflection_button, practices_button = st.columns([1, 1.2])
            with reflection_button:
                go("chat", "Start a reflection", primary=True)
            with practices_button:
                go("practices", "Explore practices")
            st.html(
                '<p class="quiet-line">No account needed. Your chat is not saved to the ratings database.</p>',
            )
        with right, st.container(key="home_pause"):
            st.html(
                '<div class="practice-heading">'
                '<span class="eyebrow">BREATHING EXERCISE</span>'
                '<h2>Take a minute.</h2>'
                '<p>Choose your time, then press Begin.</p>'
                '</div>',
            )
            breathing_timer()

    with st.container(key="home_pathways"):
        section_title("WHAT YOU CAN DO", "What would help today?", "Start with whichever feels useful.")
        values = [
            {
                "label": "01 / CHECK IN",
                "title": "Record how you feel",
                "text": "Rate your mood, stress and energy, then see how your ratings change over time.",
                "page": "checkin",
                "action": "Take a check-in →",
            },
            {
                "label": "02 / WRITE",
                "title": "Write it down",
                "text": "Write with a prompt or start from scratch. Your journal stays in this session "
                "unless you download it.",
                "page": "journal",
                "action": "Open your journal →",
            },
            {
                "label": "03 / PLAN",
                "title": "Choose a next step",
                "text": "Set a goal you can act on, or use the daily checklist to remember what you want to do.",
                "page": "goals",
                "action": "Choose a small habit →",
            },
        ]
        for column, item in zip(st.columns(3, gap="large"), values):
            with column:
                st.caption(item["label"])
                st.subheader(item["title"])
                st.write(item["text"])
                page_link(item["page"], item["action"])

    with st.container(key="daily_reflection"):
        left, right = st.columns([2, 1], vertical_alignment="center", gap="large")
        with left:
            st.html(
                '<p class="eyebrow">TODAY’S REFLECTION</p>'
                f'<h2 class="reflection-question">{escape(daily_prompt())}</h2>'
                '<p>Use this prompt in your journal, or write about something else.</p>',
            )
        with right:
            go("journal", "Open your journal", key="daily_journal")

    section_title(
        "NEW ZEALAND RESOURCES",
        "Find support that fits",
        "Courses, information and practical tools from established New Zealand providers.",
    )
    for column, resource in zip(st.columns(3, gap="medium"), RESOURCES[:3]):
        with column:
            resource_card(resource, f"home_resource_{resource['id']}")
    page_link("guides", "Explore all NZ resources →")

    with st.container(key="home_philosophy"):
        left, right = st.columns([1, 1.3], gap="large")
        with left:
            st.html('<p class="eyebrow">OUR APPROACH</p><h2>Why I built KōreroPal</h2>')
        with right:
            st.write(
                "I built KōreroPal to give people a way to check in with themselves and talk "
                "through what is going on. It combines my interests in computer science and "
                "psychology.",
            )
            st.write(
                "It is a student project, and it has limits. It can help you reflect, but it "
                "cannot diagnose you or replace support from another person.",
            )
            page_link("about", "Read about the project →")
    newsletter_section()


def newsletter_section():
    url = get_secret("NEWSLETTER_URL", "")
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username:
        return
    with st.container(border=True):
        st.subheader("Project updates by email")
        st.write(
            "Choose whether to receive KōreroPal updates on our subscription page. Review its "
            "frequency, consent, privacy, and unsubscribe options before signing up. This page "
            "does not collect your email.",
        )
        st.link_button("Visit the newsletter signup", url)


def guides_page():
    intro(
        "NEW ZEALAND RESOURCES",
        "Support for student life",
        "Find existing courses and resources for stress, sleep, low mood and other things that "
        "can affect studying and everyday life.",
    )
    st.caption(
        "These links open the provider's website in a new tab. Their privacy policies and "
        "eligibility rules apply. KōreroPal does not send your chat, journal or ratings to these "
        "sites.",
    )
    left, right = st.columns([2, 1])
    query = left.text_input(
        "Search resources",
        placeholder="Try sleep, stress, or a provider's name",
        max_chars=100,
    )
    topic = right.selectbox("Choose a topic", RESOURCE_TOPICS)
    resources = filter_resources(query, topic)
    st.header("Browse resources")
    st.caption(
        f"{len(resources)} {'resource' if len(resources) == 1 else 'resources'} · Links checked 24 October 2026",
    )
    if not resources:
        st.info("No resources match that search. Try another word or choose All topics.")
    for start in range(0, len(resources), 2):
        for column, resource in zip(st.columns(2, gap="medium"), resources[start:start + 2]):
            with column:
                resource_card(resource, f"resource_{resource['id']}")
    st.header("Support through your place of study")
    st.write(
        "Your university or polytechnic may offer counselling, student health, learning support "
        "and help with financial pressure. Check its official student support page for the "
        "services available to you.",
    )
    page_link("resources", "Find someone to talk to →")
    st.caption(
        "KōreroPal is not affiliated with these providers. The Student life filter highlights "
        "resources that may be relevant to students; it does not mean the provider offers a "
        "student-only service.",
    )


def legacy_guide_page():
    st.switch_page(st.session_state.pages["guides"])


def practices_page():
    intro(
        "PRACTICES",
        "Try an exercise",
        "Use the breathing timer, work through a grounding exercise, or find a prompt to write "
        "about. You can stop at any point.",
    )
    choice = st.segmented_control(
        "Choose a practice",
        ["Breathe", "Notice your senses", "Reflect", "Wind down"],
        default="Breathe",
        key="practice_choice",
    )
    if choice == "Breathe":
        with st.container(border=True):
            left, right = st.columns([1, 1.2], gap="large", vertical_alignment="center")
            with left:
                st.caption("01 / A GENTLE PAUSE")
                st.header("Using the breathing timer")
                st.write(
                    "Settle somewhere comfortable. Use the circle as an optional guide, or let "
                    "your breath find its own pace. You can keep your eyes open.",
                )
                st.caption(
                    "The guide offers equal, gentle counts without holding your breath. Stop if "
                    "you feel dizzy or uncomfortable.",
                )
                st.markdown(
                    "[About gentle breathing · "
                    "NHS](https://www.nhs.uk/mental-health/self-help/guides-tools-and-activities/breathing-exercises-for-stress/)",
                )
            with right:
                breathing_timer()
    elif choice == "Notice your senses":
        grounding_practice()
    elif choice == "Reflect":
        st.subheader(daily_prompt())
        st.write(
            "You can think about this quietly or write a few words in your session-only journal. "
            "There is no need to turn it into a lesson.",
        )
        go("journal", "Open your journal", primary=True)
    elif choice == "Wind down":
        st.header("Getting ready to rest")
        st.write("Choose whatever fits tonight. You do not need to do all of these.")
        for number, text in enumerate(["Put one unfinished task aside for tomorrow", "Make your surroundings a little more comfortable", "Choose a quiet activity you enjoy", "Give yourself permission to stop planning"]):
            st.checkbox(text, key=f"wind_down_{number}")
        st.link_button(
            "Explore sleep resources at Just a Thought ↗",
            "https://www.justathought.co.nz/the-wellbeing-space",
        )
    section_title("FIND WHAT FITS", "A few other ways to begin.")
    pathways = [
        {
            "title": "Understand your day",
            "body": "A quick check-in for mood, stress, and energy.",
            "page": "checkin",
        },
        {
            "title": "Put thoughts somewhere",
            "body": "A session-only notebook with reflection prompts.",
            "page": "journal",
        },
        {
            "title": "Make room for a habit",
            "body": "Choose a small action that matters to you.",
            "page": "goals",
        },
    ]
    for column, item in zip(st.columns(3), pathways):
        with column:
            st.subheader(item["title"])
            st.write(item["body"])
            page_link(item["page"], 'Explore →')


def grounding_practice():
    steps = [
        (
            "Look around",
            "Notice five things you can see. They can be ordinary: a colour, an edge, a patch of light.",
        ),
        (
            "Feel supported",
            "Notice four things you can feel, such as your feet on the floor or fabric against your hand.",
        ),
        (
            "Listen gently",
            "Notice three sounds, near or far. If hearing is not accessible to you, notice three "
            "different textures instead.",
        ),
        (
            "Notice something familiar",
            "Notice two scents, or simply two things around you that feel familiar.",
        ),
        (
            "Finish where you are",
            "Notice one small thing you appreciate in this moment. You can stop here without "
            "needing to feel different.",
        ),
    ]
    index = st.session_state.get("grounding_step", 0)
    with st.container(border=True):
        st.caption(f"STEP {index + 1} OF {len(steps)} · ADAPT OR SKIP ANY SENSE")
        st.subheader(steps[index][0])
        st.write(steps[index][1])
        st.progress((index + 1) / len(steps))
        previous_button, next_button = st.columns(2)
        if previous_button.button("Previous", disabled=index == 0):
            st.session_state.grounding_step = max(0, index - 1)
            st.rerun()
        if next_button.button("Next step" if index < 4 else "Begin again", type="primary"):
            st.session_state.grounding_step = (index + 1) % len(steps)
            st.rerun()
        st.caption("An optional attention exercise, not treatment. Stop if it doesn't feel helpful.")


def remember_journal():
    st.session_state.journal_draft = st.session_state.journal_input


def clear_journal():
    st.session_state.journal_draft = ""
    st.session_state.journal_input = ""


def journal_page():
    intro(
        "JOURNAL",
        "Write what’s on your mind",
        "Use the prompt below or write about your own topic. You can download your writing or "
        "clear it when you’re finished.",
    )
    st.info(
        "Session only: your writing is held in this app session on the server. It is not saved to"
        " the database or sent to AI. Save a copy yourself if you want to keep it; refreshing or "
        "leaving can lose it.",
    )
    offset = st.session_state.get("journal_prompt_offset", 0)
    with st.container(key="journal_prompt"):
        st.caption("A PLACE TO BEGIN")
        st.subheader(daily_prompt(offset))
        if st.button("Try another prompt"):
            st.session_state.journal_prompt_offset = offset + 1
            st.rerun()
    if "journal_input" not in st.session_state:
        st.session_state.journal_input = st.session_state.get("journal_draft", "")
    st.text_area(
        "Your words",
        key="journal_input",
        height=260,
        max_chars=5000,
        on_change=remember_journal,
        placeholder="Today, I’m noticing…",
    )
    st.caption("Please leave out names, contact details, and other identifying information.")
    clear_button, download_button = st.columns([1, 2])
    clear_button.button("Clear my writing", on_click=clear_journal, disabled=not st.session_state.journal_input)
    download_button.download_button(
        "Download a private copy",
        st.session_state.journal_input,
        file_name=f"my-reflection-{local_day()}.txt",
        mime="text/plain",
        disabled=not st.session_state.journal_input,
    )
    st.caption("A download stays on your device. Take care if you use a shared computer.")


def remember_habit(index):
    st.session_state.habit_values[index] = st.session_state[f"habit_check_{index}"]


def habits_section():
    st.header("Your daily checklist")
    st.caption("Optional, session-only, and reset for a new day. Missing a day is not a failure.")
    day = str(local_day())
    if st.session_state.get("habit_day") != day:
        for key in list(st.session_state):
            if key.startswith("habit_check_"):
                del st.session_state[key]
        st.session_state.habit_day = day
        st.session_state.habit_values = {}
    if "habit_values" not in st.session_state:
        st.session_state.habit_values = {}
    habits = [
        "Make time for a pause",
        "Connect with someone",
        "Move in a way that suits me",
        "Make room for rest",
    ]
    values = []
    for index, label in enumerate(habits):
        key = f"habit_check_{index}"
        if key not in st.session_state:
            st.session_state[key] = st.session_state.habit_values.get(index, False)
        values.append(st.checkbox(label, key=key, on_change=remember_habit, args=(index,)))
    st.caption(
        f"{sum(values)} of {len(values)} noticed today. This is a reminder of your choices, not a wellbeing score.",
    )


def about_page():
    intro(
        "THE PROJECT",
        "About KōreroPal",
        "A student-built wellbeing app combining computer science and psychology. Here is what it"
        " does, why it exists, and where its limits are.",
    )
    left, right = st.columns([1, 1.5], gap="large")
    with left:
        st.html(
            f'<div class="about-brand"><img src="{asset_url("logo.png")}" alt="Original KōreroPal logo" width="200" height="164"><p>Created in Aotearoa.<br>Built around small steps.</p></div>',
        )
    with right:
        st.header("Where it started")
        st.write(
            "KōreroPal was created by Nick Falkov as a university portfolio project bringing "
            "together computer science and psychology. The idea is simple: make space for people "
            "to notice how they feel, reflect in their own words, and decide on a manageable next"
            " step.",
        )
        st.write(
            "It is not a clinic, counselling provider, or government service. It is not endorsed "
            "by a university or a health agency. Its tools are for everyday reflection and "
            "general education.",
        )
    section_title("HOW IT WORKS", "What to expect")
    suggestions = [
        {
            "title": "People before metrics",
            "text": "Your ratings describe a moment. They do not define you, diagnose you, or measure your worth.",
        },
        {
            "title": "Privacy with clarity",
            "text": "Know what stays in the session, what is saved, and when a message goes to an AI provider.",
        },
        {
            "title": "Small, realistic steps",
            "text": "A useful step fits your real circumstances. There are no streak penalties or "
            "promises of transformation.",
        },
    ]
    for column, item in zip(st.columns(3), suggestions):
        with column:
            st.subheader(item["title"])
            st.write(item["text"])
    st.header("A sense of place")
    st.write(
        "The original olive logo and a restrained woven border connect the visual design to "
        "Aotearoa. The border is an original geometric treatment inspired by the interlacing "
        "structure of harakeke weaving; it does not reproduce a named iwi pattern or imply "
        "cultural endorsement.",
    )
    st.markdown("Learn about [raranga through Te Papa](https://collections.tepapa.govt.nz/topic/3647).")
    page_link("privacy", "Understand how your information is handled →")


def build_feedback_link(topic, subject, message, consent, website=""):
    if website:
        raise ValueError("The form could not be prepared. Please try again.")
    if not consent:
        raise ValueError("Please confirm that your report contains no private information.")
    if not 5 <= len(subject.strip()) <= 100:
        raise ValueError("Please write a subject between 5 and 100 characters.")
    if not 20 <= len(message.strip()) <= 1500:
        raise ValueError("Please write a description between 20 and 1,500 characters.")
    body = f"Topic: {topic}\n\n{message.strip()}"
    return "https://github.com/nfal707/KoreroPal/issues/new?" + urlencode({"title": subject.strip(), "body": body})


def contact_page():
    intro(
        "CONTACT & FEEDBACK",
        "Report a problem or suggest a change",
        "Report a technical problem, suggest an improvement, or flag something that isn’t accessible.",
    )
    st.warning(
        "Feedback uses the public GitHub issue tracker. Do not include wellbeing information, "
        "chat text, recovery codes, keys, or contact details. This is not a support or crisis "
        "channel.",
    )
    with st.form("feedback_form"):
        topic = st.selectbox(
            "What is your feedback about?",
            ["Technical problem", "Accessibility", "Content correction", "Suggestion"],
        )
        subject = st.text_input(
            "Short subject",
            max_chars=100,
            placeholder="For example: A button is clipped on mobile",
        )
        message = st.text_area(
            "What would you like us to know?",
            max_chars=1500,
            placeholder="Describe the issue without including private information.",
        )
        website = st.text_input(
            "Leave this field empty",
            key="feedback_website",
            help="Spam prevention. Please leave empty.",
        )
        consent = st.checkbox(
            "My report contains no private information. I understand that submitting it on GitHub"
            " makes it public.",
        )
        submitted = st.form_submit_button("Prepare my report", type="primary")
    if submitted:
        try:
            url = build_feedback_link(topic, subject, message, consent, website)
            st.success(
                "Your report is ready to review. Nothing has been sent. Open GitHub to review and"
                " submit it; a GitHub account is required.",
            )
            st.link_button("Review report on GitHub ↗", url)
        except ValueError as error:
            st.error(str(error))
    email = get_secret("CONTACT_EMAIL", "")
    if re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        st.link_button("Email the project", f"mailto:{email}")
    st.subheader("Looking for wellbeing support?")
    st.write(
        "Please contact an appropriate support service rather than leaving a public report. "
        "KōreroPal does not monitor feedback for urgent help.",
    )
    page_link("resources", "Find real support →")


def faq_page():
    intro(
        "HELP",
        "Common questions",
        "What KōreroPal does, what it doesn’t, and how to make it work for you.",
    )
    questions = [
        (
            "Is this therapy?",
            "No. KōreroPal is a student-built reflection tool and educational resource. It cannot"
            " diagnose, provide treatment, or replace professional or crisis support.",
        ),
        (
            "Do I need an account?",
            "No. A private recovery code links your saved numerical ratings. Keep it safe: anyone"
            " with it can open those ratings. It is not an authenticated account.",
        ),
        (
            "Where does my chat go?",
            "When AI is configured, your current message, up to eight recent messages, and up to "
            "three recent check-ins go to Groq. The app asks for consent before chat. Chat text "
            "is not saved in the KōreroPal ratings database.",
        ),
        (
            "Why am I seeing built-in prompts?",
            "If Groq is not configured or a request fails, KōreroPal uses simpler built-in "
            "prompts. These are more limited than an AI conversation, and the interface makes "
            "that clear.",
        ),
        (
            "When do I get my reflection results?",
            "Choose End chat or type end chat. Then enter your own final ratings. The summary "
            "compares your before-and-after ratings; AI does not rank or diagnose you.",
        ),
        (
            "Will my journal and habits be here next time?",
            "They are session-only. They may disappear on refresh, after disconnection, or when "
            "the session ends. The recovery code restores saved ratings, not writing or habit "
            "checklists. You can explicitly download your journal.",
        ),
        (
            "Can I delete my saved ratings?",
            "The current portfolio app does not offer self-service deletion. Do not post recovery"
            " codes or deletion details publicly. A private owner-managed process and retention "
            "policy are required before participant recruitment.",
        ),
        (
            "Does the site use cookies or advertising?",
            "The app uses necessary session and security mechanisms. Streamlit usage telemetry is"
            " disabled in this project, and no optional analytics or advertising scripts have "
            "been added. Hosting providers may still process connection metadata.",
        ),
    ]
    for title, answer in questions:
        with st.expander(title):
            st.write(answer)
    page_link("contact", "Something still unclear? →")


def terms_page():
    intro(
        "PROJECT INFORMATION",
        "Terms of use",
        "Last updated 24 October 2026. Please read these practical limits before using the project.",
    )
    for title, text in [
        ("What the project offers", "KōreroPal offers self-guided wellbeing reflection and general educational material. It is an independent portfolio project, not a medical device, treatment, diagnosis tool, or emergency service."),
        ("Use your judgement", "AI can be inaccurate, incomplete, or inappropriate. You choose whether a suggestion fits your circumstances. Do not rely on the app for health decisions, medication advice, or urgent support; seek a qualified professional."),
        ("Respect the space", "Do not use the app to harm others, attempt unauthorised access, expose private information, or overload the service. Never enter another person's private information or recovery code."),
        ("Availability and your writing", "Features may change, be interrupted, or become unavailable. Session-only writing is temporary. Download anything you choose to retain, and keep recovery codes private."),
        ("External services and links", "Groq processes AI requests when enabled. Hosting, database, GitHub, and any configured newsletter service have their own terms and privacy practices. Opening an external link takes you to that service."),
        ("About this notice", "These terms describe this portfolio project's current operation and limits. They are not a claim of legal, clinical, or regulatory certification and do not remove rights that apply under law."),
    ]:
        st.subheader(title)
        st.write(text)
    page_link("privacy", "Read the privacy information →")


def accessibility_page():
    intro(
        "USING THE SITE",
        "Accessibility",
        "KōreroPal aims to make everyday reflection usable with different devices, abilities, and"
        " preferences.",
    )
    st.subheader("What you can expect")
    st.write(
        "Keyboard-operable controls, visible focus indicators, labelled inputs, responsive "
        "layouts, readable contrast, and text explanations alongside colour. Browser zoom is "
        "supported. The breathing guide respects reduced-motion settings and can be paused or "
        "reset.",
    )
    st.subheader("Choose what works for you")
    st.write(
        "Keep your eyes open during practices if you prefer. Adapt or skip sensory prompts. You "
        "can use reflection and journaling without completing a breathing exercise, and no "
        "practice starts automatically.",
    )
    st.subheader("Our current limits")
    st.write(
        "The project is designed towards WCAG 2.2 AA, but has not had an independent "
        "accessibility audit. Screen-reader behaviour depends partly on Streamlit and the "
        "browser. The breathing timer is an embedded interactive region; its written instructions"
        " remain available outside it.",
    )
    st.subheader("Tell us about a barrier")
    st.write(
        "If a control is difficult to use or content is hard to understand, describe the barrier "
        "through the feedback page. Keep personal and wellbeing information out of public "
        "reports.",
    )
    page_link("contact", "Report an accessibility issue →")
