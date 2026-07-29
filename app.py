import re
import secrets
import string
import uuid

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from core.ai import generate_support_response, groq_available
from core.config import APP_NAME, NZ_RESOURCES
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


def page_header():
    st.markdown(
        """
        <style>
        .stApp {
            background: linear-gradient(180deg, #F4FAF7 0%, #EAF4EF 100%);
            color: #1F332B;
        }

        section[data-testid="stSidebar"] {
            background-color: #DDEDE5;
        }

        .main-title {
            font-size: 42px;
            font-weight: 700;
            color: #2F6F5E;
            margin-bottom: 0;
        }

        .subtitle {
            color: #4D6B60;
            font-size: 17px;
            margin-top: 0;
        }

        .project-note {
            background-color: #FFF8E7;
            border-left: 5px solid #D6A84F;
            padding: 12px;
            border-radius: 10px;
            color: #4A3B1F;
            margin-bottom: 18px;
        }

        .privacy-note {
            background-color: #EEF8F4;
            border-left: 5px solid #5E9C87;
            padding: 12px;
            border-radius: 10px;
            color: #294A3E;
            margin-bottom: 18px;
        }

        .stButton > button {
            background-color: #5E9C87;
            color: white;
            border-radius: 12px;
            border: none;
            padding: 0.6rem 1rem;
        }

        .stButton > button:hover {
            background-color: #497F6D;
            color: white;
        }

        div[data-baseweb="select"] > div {
            background-color: #F7FCFA;
            border-radius: 12px;
            border: 1px solid #B7D5C8;
        }

        textarea, input {
            border-radius: 12px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<p class="main-title">KōreroPal</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="subtitle">A calm wellbeing reflection app for talking, tracking, and taking the next small step.</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="project-note">
        <b>University project:</b> KōreroPal is a student-built portfolio project.
        It is not made by, endorsed by, or affiliated with the New Zealand Ministry of Education,
        Ministry of Health, University of Auckland, or any official support service.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.warning(
        "KōreroPal is not a therapist, doctor, counsellor, crisis service, or diagnosis tool. "
        "If you are in immediate danger in New Zealand, call 111."
    )


def create_anonymous_id():
    characters = string.ascii_uppercase + string.digits
    code = "".join(secrets.choice(characters) for _ in range(10))
    return f"KP-{code}"


def valid_anonymous_id(value):
    return bool(re.fullmatch(r"KP-[A-Z0-9]{10}", value or ""))


def get_anonymous_id():
    if "anonymous_id" in st.session_state:
        return st.session_state.anonymous_id

    query_id = st.query_params.get("study")

    if valid_anonymous_id(query_id):
        anonymous_id = query_id
    else:
        anonymous_id = create_anonymous_id()
        st.query_params["study"] = anonymous_id

    st.session_state.anonymous_id = anonymous_id
    return anonymous_id


def reset_session_data():
    st.session_state.chat_history = []
    st.session_state.before_ratings = None
    st.session_state.interaction_id = None


def initialise_session_data():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "before_ratings" not in st.session_state:
        st.session_state.before_ratings = None

    if "interaction_id" not in st.session_state:
        st.session_state.interaction_id = None

    if "goals" not in st.session_state:
        st.session_state.goals = []

    if "evaluation_saved" not in st.session_state:
        st.session_state.evaluation_saved = False


def sidebar(anonymous_id):
    st.sidebar.title("KōreroPal")

    if groq_available():
        st.sidebar.success("AI service active")
    else:
        st.sidebar.info("Safe fallback mode active")

    st.sidebar.caption(f"Data storage: {database_name()}")

    st.sidebar.subheader("Anonymous study code")
    st.sidebar.code(anonymous_id)
    st.sidebar.caption(
        "Bookmark this page or save this code to keep your anonymous results linked over time. "
        "Do not replace it with your name or student ID."
    )

    if st.sidebar.button("Create a new anonymous code"):
        anonymous_id = create_anonymous_id()
        st.session_state.anonymous_id = anonymous_id
        st.query_params["study"] = anonymous_id
        reset_session_data()
        st.rerun()

    page = st.sidebar.selectbox(
        "Choose a page",
        [
            "Home",
            "Daily Check-in",
            "AI Support Chat",
            "My Dashboard",
            "Project Results",
            "Coping Toolkit",
            "Small Goals",
            "NZ Resources",
            "Privacy and About",
        ],
    )

    return page


def home_page():
    st.header("Welcome")
    st.write(
        "KōreroPal is a student-built wellbeing reflection project. It combines anonymous "
        "Likert tracking with a supportive AI conversation and practical coping strategies."
    )

    st.subheader("What you can do")
    st.write("- Record mood, stress, and energy on 1–7 scales")
    st.write("- Compare ratings before and after an AI reflection session")
    st.write("- Track your anonymous results over time")
    st.write("- Rate whether KōreroPal felt relevant and supportive")
    st.write("- Use coping strategies and session-only goals")

    st.markdown(
        """
        <div class="privacy-note">
        <b>Data design:</b> KōreroPal does not ask for a name, email, student ID, phone number,
        exact address, journal entry, or demographic information. Chat text and goals are not
        written to the KōreroPal database. Only anonymous 1–7 ratings and timestamps are saved.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "When AI mode is active, your current message, recent session conversation, and up to three "
        "recent anonymous check-ins, including their timestamps and ratings, are sent to Groq to generate a response. "
        "Do not enter identifying or highly private information."
    )


def checkin_page(anonymous_id):
    st.header("Daily Check-in")
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
    st.subheader("1. Rate how you feel before chatting")

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

        submitted = st.form_submit_button("Start reflection")

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
        st.session_state.chat_history = []
        st.rerun()


def display_chat_history():
    for item in st.session_state.chat_history:
        if item["role"] == "user":
            st.markdown(f"**You:** {item['content']}")
        else:
            st.markdown(f"**KōreroPal:** {item['content']}")

        st.divider()


def chat_form(anonymous_id):
    st.subheader("2. Talk with KōreroPal")
    st.caption(
        "The conversation is kept only in this active session and is not saved in the KōreroPal database. "
        "Avoid names, contact details, student IDs, or exact locations."
    )

    if st.session_state.chat_history:
        display_chat_history()

    with st.form("chat_form", clear_on_submit=True):
        message = st.text_area(
            "What's on your mind?",
            height=140,
            placeholder="Example: I feel overwhelmed by the amount of work I need to do.",
        )
        submitted = st.form_submit_button("Send")

    if submitted:
        if not message.strip():
            st.warning("Write a message first.")
            return

        try:
            checkins = load_daily_checkins(anonymous_id)
            recent_context = recent_context_from_checkins(checkins)
        except DatabaseConnectionError as error:
            st.warning(f"{error} The chat can still continue without recent check-in context.")
            recent_context = ""
        previous_history = st.session_state.chat_history.copy()

        response, risk = generate_support_response(
            message.strip(),
            recent_context=recent_context,
            conversation_history=previous_history,
        )

        st.session_state.chat_history.append(
            {"role": "user", "content": message.strip()}
        )
        st.session_state.chat_history.append(
            {"role": "assistant", "content": response, "risk": risk}
        )
        st.rerun()


def finish_reflection_form(anonymous_id):
    if not st.session_state.chat_history:
        return

    st.subheader("3. Rate the session")
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

        submitted = st.form_submit_button("Save anonymous evaluation")

    if submitted:
        before = st.session_state.before_ratings

        try:
            save_evaluation_session(
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
            reset_session_data()
            st.session_state.evaluation_saved = True
            st.rerun()
        except DatabaseConnectionError as error:
            st.error(str(error))
        except Exception:
            st.error("The evaluation could not be saved. Please try again.")


def chat_page(anonymous_id):
    st.header("AI Support Chat")

    if st.session_state.evaluation_saved:
        st.success("Anonymous session evaluation saved. The chat has been cleared.")
        st.session_state.evaluation_saved = False
    st.write(
        "This page measures mood, stress, and energy before and after a reflection session, "
        "then asks three 1–7 questions about KōreroPal's performance."
    )

    if groq_available():
        st.info(
            "AI mode is active. Your current message, recent session conversation, and up to three recent anonymous "
            "check-ins, including their timestamps and ratings, are sent to Groq. KōreroPal does not save the chat text."
        )
    else:
        st.info(
            "The external AI service is not configured, so KōreroPal will use its built-in response system."
        )

    if st.session_state.before_ratings is None:
        start_reflection_form()
        return

    before = st.session_state.before_ratings
    st.caption(
        f"Session-only starting ratings: mood {before['mood']}/7, "
        f"stress {before['stress']}/7, energy {before['energy']}/7"
    )

    chat_form(anonymous_id)
    finish_reflection_form(anonymous_id)

    if st.button("Cancel and clear this session"):
        reset_session_data()
        st.rerun()


def my_dashboard_page(anonymous_id):
    st.header("My Anonymous Dashboard")

    try:
        checkins = load_daily_checkins(anonymous_id)
        evaluations = load_evaluation_sessions(anonymous_id)
    except DatabaseConnectionError as error:
        st.error(str(error))
        return

    if checkins.empty and evaluations.empty:
        st.info("No anonymous ratings have been saved for this study code yet.")
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


def project_results_page():
    st.header("Anonymous Project Results")
    st.write(
        "This page shows aggregate results only. It does not display chat text, names, contact details, or anonymous study codes."
    )

    try:
        checkins = load_daily_checkins()
        evaluations = load_evaluation_sessions()
    except DatabaseConnectionError as error:
        st.error(str(error))
        return

    col1, col2 = st.columns(2)
    col1.metric("Anonymous daily check-ins", len(checkins))
    col2.metric("Completed AI evaluations", len(evaluations))

    if evaluations.empty:
        st.info("No completed AI evaluations yet.")
        return

    evaluations = add_change_columns(evaluations)

    st.subheader("Average change after using KōreroPal")
    col1, col2, col3 = st.columns(3)
    col1.metric("Mood", f"{evaluations['mood_change'].mean():+.2f}")
    col2.metric("Stress improvement", f"{evaluations['stress_improvement'].mean():+.2f}")
    col3.metric("Energy", f"{evaluations['energy_change'].mean():+.2f}")

    st.subheader("Average companion ratings")
    col1, col2, col3 = st.columns(3)
    col1.metric("Felt heard", f"{evaluations['felt_heard'].mean():.2f}/7")
    col2.metric(
        "Response relevance",
        f"{evaluations['response_relevance'].mean():.2f}/7",
    )
    col3.metric(
        "Would use again",
        f"{evaluations['would_use_again'].mean():.2f}/7",
    )

    st.caption(
        "These results are descriptive project analytics. They do not establish clinical effectiveness or causation."
    )


def toolkit_page():
    st.header("Coping Toolkit")

    for key in STRATEGIES:
        strategy = STRATEGIES[key]

        with st.expander(strategy["title"]):
            st.write(format_strategy(strategy))


def goals_page():
    st.header("Small Goals")
    st.write(
        "Goals are kept only in this active session. They are not written to the database and disappear when the session ends."
    )

    with st.form("goal_form", clear_on_submit=True):
        goal = st.text_input(
            "Add a small goal",
            placeholder="Example: Do one practice question",
        )
        submitted = st.form_submit_button("Add goal")

    if submitted and goal.strip():
        st.session_state.goals.append(
            {
                "id": str(uuid.uuid4()),
                "goal": goal.strip(),
                "status": "active",
            }
        )
        st.success("Session-only goal added.")

    if not st.session_state.goals:
        st.info("No session-only goals yet.")
        return

    for item in st.session_state.goals:
        col1, col2 = st.columns([4, 1])
        col1.write(f"{item['goal']} ({item['status']})")

        if item["status"] != "complete":
            if col2.button("Done", key=f"done_{item['id']}"):
                item["status"] = "complete"
                st.rerun()


def resources_page():
    st.header("NZ Support Resources")

    for resource in NZ_RESOURCES:
        st.subheader(resource["name"])
        st.write(f"**Contact:** {resource['contact']}")
        st.write(f"**Use when:** {resource['when']}")


def privacy_page():
    st.header("Privacy and About")

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
        "The anonymous study code is placed in the page URL so the same browser bookmark can reopen the same anonymous record. "
        "Dashboard download buttons save a local CSV copy through the browser. The current chat, temporary before-session ratings, "
        "and goals are held only in active app-session memory and are not written to the study database."
    )

    st.subheader("External processing")
    st.write(
        "When Groq AI is enabled, the current message, recent session conversation, and up to three recent anonymous "
        "check-ins, including their timestamps and ratings, are sent to Groq to generate a response. "
        "Users should not enter identifying or highly private details. Hosting and AI providers may process technical metadata under their own terms."
    )

    st.subheader("Study limitations")
    st.write(
        "KōreroPal's ratings are anonymous self-report project data. The results are descriptive and cannot show that KōreroPal caused a change in wellbeing. "
        "KōreroPal is not a medical device, treatment, diagnostic tool, or replacement for professional support."
    )


def main():
    st.set_page_config(page_title=APP_NAME, page_icon="💬", layout="centered")
    init_db()
    initialise_session_data()

    anonymous_id = get_anonymous_id()

    page_header()
    page = sidebar(anonymous_id)

    if page == "Home":
        home_page()
    elif page == "Daily Check-in":
        checkin_page(anonymous_id)
    elif page == "AI Support Chat":
        chat_page(anonymous_id)
    elif page == "My Dashboard":
        my_dashboard_page(anonymous_id)
    elif page == "Project Results":
        project_results_page()
    elif page == "Coping Toolkit":
        toolkit_page()
    elif page == "Small Goals":
        goals_page()
    elif page == "NZ Resources":
        resources_page()
    elif page == "Privacy and About":
        privacy_page()


if __name__ == "__main__":
    main()
