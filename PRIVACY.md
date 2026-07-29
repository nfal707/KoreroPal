# KōreroPal privacy and data note

## Purpose

KōreroPal collects anonymous Likert ratings to examine changes in self-reported mood, stress, and energy and to describe how users rate the AI companion over repeated sessions.

## Application database fields

### Daily check-ins

- anonymous study code
- date and time
- mood from 1 to 7
- stress from 1 to 7
- energy from 1 to 7

### AI session evaluations

- anonymous study code
- random interaction ID
- date and time
- mood, stress, and energy before the conversation
- mood, stress, and energy after the conversation
- felt heard rating from 1 to 7
- response relevance rating from 1 to 7
- willingness to use again rating from 1 to 7

## Data not saved by KōreroPal

- name
- email address
- phone number
- student ID
- exact address
- demographic information
- journal text
- chat messages
- AI responses
- goal text

## Session and browser behaviour

The anonymous study code appears in the page URL. A user can bookmark that URL to reconnect the same anonymous record or create a new code at any time. The dashboard can download CSV files to the user's device through the browser.

Chat history, temporary before-session ratings, and goals are held only in active Streamlit session memory. They are cleared when the session is reset and are not inserted into the KōreroPal study tables.

## External services

When AI mode is active, Groq receives the current message, up to eight recent messages from the active session, and up to three recent anonymous check-ins, including their timestamps and ratings. The anonymous study code is not included in the AI prompt. Groq processes this information to generate a response.

Streamlit hosts the application and Supabase hosts the anonymous rating tables. These providers may process technical or operational metadata under their own terms. Users should not enter identifying or highly private information into the chat.

## Research and ethics note

Removing direct identifiers does not automatically make wellbeing data risk-free or exempt a project from ethics requirements. Before inviting real participants, confirm the approved purpose, consent wording, access controls, retention period, deletion process, recruitment method, and whether institutional ethics review is required.

## Interpretation

The dashboard presents descriptive self-report results. Before and after changes do not prove that KōreroPal caused an improvement and should not be described as treatment effectiveness.
