from pathlib import Path
import uuid

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from core.ai import groq_available
from core.config import APP_NAME, MAX_CHAT_TURNS, MAX_MESSAGE_LENGTH, NZ_RESOURCES, SAFETY_NOTICE
from core.identity import create_anonymous_id, valid_anonymous_id
from core.reflection import create_chat, is_end_chat, send_message
from core.safety import assess_risk, crisis_response
from core.database import (
    DatabaseConnectionError,
    database_name,
    init_db,
    load_daily_checkins,
    load_evaluation_sessions,
    save_daily_checkin,
    save_evaluation_session,
)
from core.summaries import (
    add_change_columns,
    daily_summary,
    evaluation_summary,
    recent_context_from_checkins,
)
from core.strategies import STRATEGIES, format_strategy
from core import website
from core.content import LEGACY_GUIDE_PATHS
from core.ui import brand_header, footer, intro, safety_note, STATIC


ASSETS = Path(__file__).resolve().parent / "assets"


def page_header():
    brand_header()
    safety_note()


def get_anonymous_id():
    query_id = st.query_params.get("study")

    if "anonymous_id" not in st.session_state:
        st.session_state.anonymous_id = query_id if valid_anonymous_id(query_id) else create_anonymous_id()

    if "study" in st.query_params:
        del st.query_params["study"]

    return st.session_state.anonymous_id


def reset_session_data():
    st.session_state.chat = create_chat()
    st.session_state.before_ratings = None
    st.session_state.interaction_id = None
    st.session_state.chat_phase = "before"
    st.session_state.session_results = None


def initialise_session_data():
    if "chat" not in st.session_state:
        reset_session_data()

    if "goals" not in st.session_state:
        st.session_state.goals = []


def switch_identity(code):
    st.session_state.anonymous_id = code
    st.session_state.goals = []
    reset_session_data()
    for key in list(st.session_state):
        if key.startswith(("support_", "journal_", "habit_", "wind_down_")):
            del st.session_state[key]


def sidebar(anonymous_id):
    st.sidebar.image(str(STATIC / "logo.png"), width=110)
    st.sidebar.caption("Your reflections, journal and check-ins.")

    with st.sidebar.expander("Your private recovery code"):
        st.caption(
            "Save this somewhere private to return to your ratings. Anyone with this code can "
            "open them. A bookmark alone won't restore them.",
        )
        st.code(anonymous_id, wrap_lines=True)
        with st.form("restore_code_form"):
            code = st.text_input("Use an existing code", type="password", max_chars=43)
            restore = st.form_submit_button("Restore my ratings")
        if restore:
            code = code.strip().upper()
            if valid_anonymous_id(code):
                switch_identity(code)
                st.rerun()
            else:
                st.error("That code doesn't look right. Please copy the complete KP- code.")
        if st.button("Start with a new code"):
            switch_identity(create_anonymous_id())
            st.rerun()

    with st.sidebar.expander("About this space"):
        st.caption(
            "Student-built university portfolio project. Not affiliated with any university, "
            "government agency, or official support service.",
        )
        st.caption("AI reflection configured" if groq_available() else "Built-in reflection mode")
        st.caption(f"Ratings storage: {database_name()}")

    st.sidebar.markdown("**Need a person to talk to?**")
    st.sidebar.page_link(
        st.session_state.pages["resources"],
        label="Find real support",
        icon=":material/favorite:",
    )
    st.sidebar.caption("Chat and goals stay in this session. Saved ratings stay linked to your private code.")


def checkin_page(anonymous_id):
    intro(
        "A MOMENT FOR YOU",
        "How are you arriving today?",
        "Notice where you are, without needing to be anywhere else. Your own ratings, at your own"
        " pace.",
    )
    st.write(
        "This saves only three anonymous 1–7 ratings. No journal text, sleep data, name, or contact details are collected."
    )

    with st.form("checkin_form", clear_on_submit=True):
        mood = st.slider(
            "Mood: 1 = very low, 7 = very positive",
            1,
            7,
            4,
        )
        stress = st.slider(
            "Stress: 1 = very calm, 7 = extremely stressed",
            1,
            7,
            4,
        )
        energy = st.slider(
            "Energy: 1 = no energy, 7 = very energised",
            1,
            7,
            4,
        )

        submitted = st.form_submit_button("Save anonymous check-in")

    if submitted:
        try:
            save_daily_checkin(anonymous_id, mood, stress, energy)
            st.success("Anonymous check-in saved.")
        except DatabaseConnectionError as error:
            st.error(str(error))
        except Exception:
            st.error("The check-in could not be saved. Please try again.")


def start_reflection_form():
    st.subheader("First, a quick check-in")
    st.write("There is no right answer. These starting ratings help you notice any change at the end.")

    with st.form("before_chat_form"):
        mood = st.slider(
            "Mood before: 1 = very low, 7 = very positive",
            1,
            7,
            4,
        )
        stress = st.slider(
            "Stress before: 1 = very calm, 7 = extremely stressed",
            1,
            7,
            4,
        )
        energy = st.slider(
            "Energy before: 1 = no energy, 7 = very energised",
            1,
            7,
            4,
        )
        consent = st.checkbox(
            "I understand that my current message, recent session conversation, and up to three recent anonymous "
            "check-ins, including their timestamps and ratings, may be sent to Groq when AI mode is active."
        )

        submitted = st.form_submit_button("Start reflection", type="primary")

    if submitted:
        if not consent:
            st.warning("Please confirm the data notice before starting.")
            return

        st.session_state.before_ratings = {
            "mood": mood,
            "stress": stress,
            "energy": energy,
        }
        st.session_state.interaction_id = str(uuid.uuid4())
        st.session_state.chat = create_chat()
        st.session_state.chat_phase = "chat"
        st.rerun()


def display_chat_history():
    """Display the current session conversation without loading external content."""

    for item in st.session_state.chat["history"]:
        role = item["role"]
        with st.chat_message(role, avatar=str(STATIC / "logo.png") if role == "assistant" else ":material/person:"):
            if item.get("risk") == "crisis":
                st.markdown(crisis_response())
            else:
                st.text(item["content"])


def end_chat():
    if not st.session_state.chat["busy"]:
        st.session_state.chat_phase = "after"


def chat_form(anonymous_id):
    """Keep the conversation and its input together in one space."""

    chat = st.session_state.chat
    with st.container(border=True):
        title, action = st.columns([3, 1])
        title.subheader("Your reflection space")
        action.button("End chat", on_click=end_chat, disabled=chat["busy"], width="stretch")
        st.caption(
            "Talk for a while, or just a moment. Choose End chat, or type it, when you're ready "
            "to reflect.",
        )
        with st.container(height=420):
            if not chat["history"]:
                with st.chat_message("assistant", avatar=str(STATIC / "logo.png")):
                    st.write(
                        "What's taking up space in your mind today? You can start wherever feels easiest.",
                    )
            display_chat_history()

        turn = len(chat["history"]) // 2
        input_key = f"support_{st.session_state.interaction_id}_{turn}"
        message = st.chat_input(
            "What's on your mind?",
            key=input_key,
            max_chars=MAX_MESSAGE_LENGTH,
            disabled=chat["busy"],
        )
        st.caption(f"{turn} of {MAX_CHAT_TURNS} turns · Chat text is not saved to the ratings database")

    if not message or not message.strip():
        return

    if is_end_chat(message):
        end_chat()
        st.rerun()

    # Only load rating context once for this submitted turn.
    recent_context = ""
    if assess_risk(message) != "crisis":
        try:
            checkins = load_daily_checkins(anonymous_id)
            recent_context = recent_context_from_checkins(checkins)
        except DatabaseConnectionError:
            pass

    try:
        with st.spinner("Taking a moment to reflect..."):
            send_message(chat, input_key, message, recent_context)
        st.rerun()
    except ValueError as error:
        st.warning(str(error))


def finish_reflection_form(anonymous_id):
    st.subheader("How are you feeling now?")
    st.caption("These are your own ratings, not a diagnosis or a score assigned by AI.")
    st.write(
        "Submitting this form saves only these anonymous ratings. Your conversation is not included."
    )

    with st.form("after_chat_form"):
        mood_after = st.slider(
            "Mood after: 1 = very low, 7 = very positive",
            1,
            7,
            4,
        )
        stress_after = st.slider(
            "Stress after: 1 = very calm, 7 = extremely stressed",
            1,
            7,
            4,
        )
        energy_after = st.slider(
            "Energy after: 1 = no energy, 7 = very energised",
            1,
            7,
            4,
        )
        felt_heard = st.slider(
            "KōreroPal helped me feel heard: 1 = strongly disagree, 7 = strongly agree",
            1,
            7,
            4,
        )
        response_relevance = st.slider(
            "KōreroPal's responses were relevant: 1 = strongly disagree, 7 = strongly agree",
            1,
            7,
            4,
        )
        would_use_again = st.slider(
            "I would use KōreroPal again: 1 = strongly disagree, 7 = strongly agree",
            1,
            7,
            4,
        )

        submitted = st.form_submit_button("Save and see my reflection", type="primary")

    if submitted:
        before = st.session_state.before_ratings

        try:
            saved = save_evaluation_session(
                st.session_state.interaction_id,
                anonymous_id,
                before["mood"],
                before["stress"],
                before["energy"],
                mood_after,
                stress_after,
                energy_after,
                felt_heard,
                response_relevance,
                would_use_again,
            )
            st.session_state.session_results = {
                "before": {name: saved[f"{name}_before"] for name in ["mood", "stress", "energy"]},
                "after": {name: saved[f"{name}_after"] for name in ["mood", "stress", "energy"]},
            }
            st.session_state.chat = create_chat()
            st.session_state.chat_phase = "complete"
            st.rerun()
        except DatabaseConnectionError as error:
            st.error(str(error))
        except Exception:
            st.error("The evaluation could not be saved. Please try again.")


def reflection_results():
    st.subheader("A moment to notice")
    st.success("Your ratings are saved. The conversation has been cleared.")
    result = st.session_state.session_results
    columns = st.columns(3)
    for column, name in zip(columns, ["mood", "stress", "energy"]):
        before = result["before"][name]
        after = result["after"][name]
        column.metric(
            name.title(),
            f"{after}/7",
            f"{after - before:+} from {before}/7",
            delta_color="inverse" if name == "stress" else "normal",
        )
    st.write(
        "Feeling the same, better, or worse are all things worth noticing. These ratings describe"
        " this moment; they don't measure your worth or prove that the conversation caused a "
        "change.",
    )
    st.page_link(st.session_state.pages["goals"], label="Choose one small next step", icon=":material/flag:")
    st.page_link(
        st.session_state.pages["dashboard"],
        label="See your reflections over time",
        icon=":material/monitoring:",
    )
    if st.button("Start another reflection", type="primary"):
        reset_session_data()
        st.rerun()


def chat_page(anonymous_id):
    intro(
        "REFLECTION",
        "Talk it through",
        "Check in before you start, then chat at your own pace. Choose End chat when you’re ready"
        " to review how you feel.",
    )
    phase = st.session_state.chat_phase
    steps = {
        "before": "① Check in   →   ② Chat   →   ③ Reflect",
        "chat": "✓ Checked in   →   ② Chat   →   ③ Reflect",
        "after": "✓ Checked in   →   ✓ Chat ended   →   ③ Reflect",
        "complete": "✓ Check-in   →   ✓ Conversation   →   ✓ Reflection saved",
    }
    st.markdown(f'<div class="step-line">{steps[phase]}</div>', unsafe_allow_html=True)

    if phase == "before":
        with st.container(border=True):
            start_reflection_form()
        return

    if phase == "complete":
        reflection_results()
        return

    if phase == "chat":
        if not groq_available():
            st.info("Built-in mode: simple reflection prompts are available while AI is not configured.")
        chat_form(anonymous_id)
    else:
        with st.expander("Review this conversation"):
            display_chat_history()
        finish_reflection_form(anonymous_id)
        if st.button("Return to chat"):
            st.session_state.chat_phase = "chat"
            st.rerun()

    with st.expander("Clear this reflection"):
        st.caption("This clears the conversation and unsaved ratings from this session.")
        if st.button("Discard and start again", disabled=st.session_state.chat["busy"]):
            reset_session_data()
            st.rerun()


def my_dashboard_page(anonymous_id):
    intro(
        "NOTICE THE PATTERNS",
        "Your wellbeing over time.",
        "Your own ratings, at your own pace. A change is something to notice, not a judgement.",
    )

    try:
        checkins = load_daily_checkins(anonymous_id)
        evaluations = load_evaluation_sessions(anonymous_id)
    except DatabaseConnectionError as error:
        st.error(str(error))
        return

    if checkins.empty and evaluations.empty:
        st.info("Your story starts with a check-in. Once you save some ratings, you'll see them here.")
        st.page_link(
            st.session_state.pages["checkin"],
            label="Take your first check-in",
            icon=":material/arrow_forward:",
        )
        return

    if not checkins.empty:
        checkins["created_at"] = pd.to_datetime(checkins["created_at"])

        st.subheader("Daily check-ins")
        col1, col2, col3 = st.columns(3)
        col1.metric("Average mood", f"{checkins['mood'].mean():.2f}/7")
        col2.metric("Average stress", f"{checkins['stress'].mean():.2f}/7")
        col3.metric("Average energy", f"{checkins['energy'].mean():.2f}/7")

        fig, ax = plt.subplots()
        ax.plot(checkins["created_at"], checkins["mood"], marker="o", label="Mood")
        ax.plot(checkins["created_at"], checkins["stress"], marker="o", label="Stress")
        ax.plot(checkins["created_at"], checkins["energy"], marker="o", label="Energy")
        ax.set_xlabel("Date")
        ax.set_ylabel("Likert rating (1–7)")
        ax.set_ylim(1, 7)
        ax.legend()
        fig.autofmt_xdate()
        st.pyplot(fig)
        plt.close(fig)

        st.text(daily_summary(checkins))

    if not evaluations.empty:
        evaluations["created_at"] = pd.to_datetime(evaluations["created_at"])
        evaluations = add_change_columns(evaluations)

        st.subheader("AI reflection sessions")
        col1, col2, col3 = st.columns(3)
        col1.metric(
            "Average mood change",
            f"{evaluations['mood_change'].mean():+.2f}",
        )
        col2.metric(
            "Average stress improvement",
            f"{evaluations['stress_improvement'].mean():+.2f}",
        )
        col3.metric(
            "Average energy change",
            f"{evaluations['energy_change'].mean():+.2f}",
        )

        fig2, ax2 = plt.subplots()
        ax2.plot(
            evaluations["created_at"],
            evaluations["mood_change"],
            marker="o",
            label="Mood change",
        )
        ax2.plot(
            evaluations["created_at"],
            evaluations["stress_improvement"],
            marker="o",
            label="Stress improvement",
        )
        ax2.plot(
            evaluations["created_at"],
            evaluations["energy_change"],
            marker="o",
            label="Energy change",
        )
        ax2.axhline(0, linewidth=1)
        ax2.set_xlabel("Date")
        ax2.set_ylabel("Change after session")
        ax2.legend()
        fig2.autofmt_xdate()
        st.pyplot(fig2)
        plt.close(fig2)

        st.text(evaluation_summary(evaluations))

    st.subheader("Download my anonymous ratings")

    checkin_export = checkins.copy()
    evaluation_export = evaluations.copy()

    if "anonymous_id" in checkin_export.columns:
        checkin_export = checkin_export.drop(columns=["anonymous_id"])

    if "anonymous_id" in evaluation_export.columns:
        evaluation_export = evaluation_export.drop(columns=["anonymous_id"])

    if not checkin_export.empty:
        st.download_button(
            "Download daily check-ins as CSV",
            checkin_export.to_csv(index=False),
            file_name="koreropal_daily_checkins.csv",
            mime="text/csv",
        )

    if not evaluation_export.empty:
        st.download_button(
            "Download AI evaluations as CSV",
            evaluation_export.to_csv(index=False),
            file_name="koreropal_ai_evaluations.csv",
            mime="text/csv",
        )


def toolkit_page():
    st.header("Coping Toolkit")

    for key in STRATEGIES:
        strategy = STRATEGIES[key]

        with st.expander(strategy["title"]):
            st.write(format_strategy(strategy))


def goals_page():
    intro(
        "MAKE ROOM FOR WHAT MATTERS",
        "Small steps, at your pace.",
        "Choose an action that fits your life today. It doesn’t have to be impressive to be worth"
        " doing.",
    )
    website.habits_section()
    st.divider()
    st.subheader("Something you want to work towards")
    st.write(
        "Goals are kept only in this active session. They are not written to the database and disappear when the session ends."
    )

    with st.form("goal_form", clear_on_submit=True):
        goal = st.text_input(
            "Add a small goal",
            placeholder="Example: Do one practice question",
            max_chars=200,
        )
        submitted = st.form_submit_button("Add goal")

    if submitted and len(st.session_state.goals) >= 20:
        st.info("You have 20 goals in this session. Try choosing one to focus on for now.")
    elif submitted and goal.strip():
        st.session_state.goals.append(
            {
                "id": str(uuid.uuid4()),
                "goal": goal.strip(),
                "status": "active",
            }
        )
        st.success("Session-only goal added.")

    if not st.session_state.goals:
        st.info("No goals yet. Start with something small enough to do today.")
        return

    for item in st.session_state.goals:
        col1, col2 = st.columns([4, 1])
        col1.text(f"{item['goal']} ({item['status']})")

        if item["status"] != "complete":
            if col2.button("Done", key=f"done_{item['id']}"):
                item["status"] = "complete"
                st.rerun()


def resources_page():
    intro(
        "PEOPLE YOU CAN TURN TO",
        "You don’t have to do this alone.",
        "KōreroPal is not a crisis service. These New Zealand services can help you reach a person.",
    )

    for resource in NZ_RESOURCES:
        st.subheader(resource["name"])
        st.write(f"**Contact:** {resource['contact']}")
        st.write(f"**Use when:** {resource['when']}")


def privacy_page():
    intro(
        "PRIVACY, PLAINLY EXPLAINED",
        "Know what stays, and what goes.",
        "Last updated 24 October 2026. Your words, ratings, and recovery code are handled differently.",
    )
    st.info(
        "Your journal, habits, goals, and chat are held in active server-session memory. Journal "
        "writing is never sent to AI or saved to the ratings database. Downloads stay on your "
        "device.",
    )

    st.subheader("What KōreroPal saves")
    st.write("- Anonymous study code")
    st.write("- Date and time")
    st.write("- Mood, stress, and energy ratings from 1–7")
    st.write("- Three 1–7 ratings about the AI companion")

    st.subheader("What KōreroPal does not save")
    st.write("- Names, email addresses, phone numbers, or student IDs")
    st.write("- Chat messages or AI responses")
    st.write("- Journal entries")
    st.write("- Goal text")
    st.write("- Demographic information")

    st.subheader("Client-side and session-only data")
    st.write(
        "Your private recovery code opens your saved ratings. Keep it private. New codes are not placed in URLs. "
        "Older bookmarked codes are accepted and removed from the visible URL when opened, but may remain in browser or hosting history. "
        "Dashboard download buttons save a local CSV copy through the browser. The current chat, temporary before-session ratings, "
        "and goals are held only in active app-session memory and are not written to the study database."
    )

    st.subheader("External processing")
    st.write(
        "When Groq AI is enabled, the current message, recent session conversation, and up to three recent anonymous "
        "check-ins, including their timestamps and ratings, are sent to Groq to generate a response. "
        "Users should not enter identifying or highly private details. Hosting and AI providers may process technical metadata under their own terms."
    )

    st.subheader("Cookies and connection data")
    st.write(
        "The app uses necessary session and security mechanisms. Streamlit usage telemetry is "
        "disabled, and this project adds no advertising or optional analytics scripts. Hosting "
        "and AI providers may process technical metadata under their own policies. There are no "
        "optional tracking cookies to opt into here.",
    )
    st.subheader("Retention and deletion")
    st.write(
        "The current portfolio version has no automatic expiry or self-service deletion for saved"
        " ratings. An owner-managed retention and private deletion process must be established "
        "before participant recruitment. Do not post your recovery code on the public issue "
        "tracker.",
    )
    st.subheader("Study limitations")
    st.write(
        "KōreroPal's ratings are anonymous self-report project data. The results are descriptive and cannot show that KōreroPal caused a change in wellbeing. "
        "KōreroPal is not a medical device, treatment, diagnostic tool, or replacement for professional support."
    )


def main():
    st.set_page_config(
        page_title="KōreroPal | Wellbeing App by Nick Falkov",
        page_icon=str(STATIC / "favicon.png"),
        layout="centered",
        initial_sidebar_state="collapsed",
        menu_items={
            "About": (
                "### KōreroPal\n\n"
                "An independent wellbeing reflection application combining "
                "Computer Science, Psychology and AI.\n\n"
                "**Developed by:** Nick Falkov\n\n"
                "**Technologies:** Python, Streamlit, Groq AI, SQLite and Supabase\n\n"
                "**Website:** https://koreropal.streamlit.app/\n\n"
                "**Source code:** https://github.com/nfal707/KoreroPal"
            ),
        },
    )

    try:
        init_db()
    except DatabaseConnectionError as error:
        st.error(str(error))
        st.stop()
    initialise_session_data()
    anonymous_id = get_anonymous_id()

    definitions = [
        ("home", website.home_page, "Home", "home", True, ""),
        ("practices", website.practices_page, "Practices", "practices", False, ""),
        ("guides", website.guides_page, "NZ resources", "guides", False, ""),
        ("chat", lambda: chat_page(anonymous_id), "Reflection", "support", False, ""),
        ("about", website.about_page, "About", "about", False, ""),
        ("checkin", lambda: checkin_page(anonymous_id), "Check-in", "check-in", False, "Your space"),
        ("dashboard", lambda: my_dashboard_page(anonymous_id), "Your progress", "dashboard", False, "Your space"),
        ("journal", website.journal_page, "Private journal", "journal", False, "Your space"),
        ("goals", goals_page, "Small habits", "goals", False, "Your space"),
        ("resources", resources_page, "Find support", "resources", False, "Help"),
        ("contact", website.contact_page, "Contact & feedback", "contact", False, "Help"),
        ("faq", website.faq_page, "Common questions", "faq", False, "Help"),
        ("privacy", privacy_page, "Privacy", "privacy", False, "Information"),
        ("terms", website.terms_page, "Terms of use", "terms", False, "Information"),
        ("accessibility", website.accessibility_page, "Accessibility", "accessibility", False, "Information"),
        ("toolkit", website.practices_page, "Coping toolkit", "toolkit", False, "Information"),
    ]
    pages = {}
    groups = {}
    for key, function, title, path, default, group in definitions:
        page = st.Page(
            function,
            title=title,
            url_path=path,
            default=default,
            visibility="hidden" if group == "Information" else "visible",
        )
        pages[key] = page
        groups.setdefault(group, []).append(page)

    for slug in LEGACY_GUIDE_PATHS:
        page = st.Page(website.legacy_guide_page, title="NZ resources", url_path=slug, visibility="hidden")
        pages[slug] = page
        groups["Information"].append(page)

    st.session_state.pages = pages
    navigation = st.navigation(groups, position="top")
    st.set_page_config(
        page_title=(
            "KōreroPal | Wellbeing App by Nick Falkov"
            if navigation == pages["home"]
            else f"{navigation.title} | KōreroPal by Nick Falkov"
        ),
        initial_sidebar_state="collapsed",
    )
    page_header()
    sidebar(anonymous_id)
    navigation.run()
    footer()


if __name__ == "__main__":
    main()
