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

New private recovery codes contain 160 random bits and are held in the active session, not added to the URL. Save the code privately and use the sidebar to restore ratings later. Anyone with the code can access those ratings; it is a bearer credential, not an authenticated account. Losing the code means the app cannot recover the record. Legacy ten-character codes and old bookmarked links still work. The app removes the legacy code from the visible URL on arrival, but cannot remove copies already retained in browser history, bookmarks, or hosting logs. The dashboard can download CSV files to the user's device through the browser.

Chat history, temporary before-session ratings, and goals are held only in active Streamlit session memory. Chat is cleared after saving an evaluation or discarding the reflection. Chat and goals are both cleared when switching recovery codes. They are cleared when the session ends and are not inserted into the KōreroPal study tables.

Journal writing and optional daily habit choices also stay in session memory on the server. They survive page navigation within that session, but can disappear after refresh, disconnection or session expiry. Switching recovery codes clears both. Habit choices reset on a new day in Pacific/Auckland time. Journals are never sent to the AI or saved to the ratings database. The user can clear their writing or download a text copy, which then remains on their device.

The breathing timer runs inside an embedded browser component without network requests or storage. It does not record breathing or health data. It pauses when the browser hides the page.

The contact form prepares a public GitHub issue link. Nothing is submitted until the user opens GitHub, reviews the report and submits it there. Reports must not contain private or wellbeing information. If configured, the newsletter link opens an external subscription service with its own privacy and consent controls; KōreroPal does not collect subscriber addresses itself.

Streamlit usage telemetry is disabled. The project adds no advertising scripts or optional analytics cookies. Necessary hosting, session and security mechanisms may still process connection data.

## External services

When AI mode is active, Groq receives the current message, up to eight recent messages from the active session, and up to three recent anonymous check-ins, including their timestamps and ratings. The anonymous study code is not included in the AI prompt. Groq processes this information to generate a response.

Streamlit hosts the application and Supabase hosts the anonymous rating tables. These providers may process technical or operational metadata under their own terms. Users should not enter identifying or highly private information into the chat.

## Research and ethics note

Removing direct identifiers does not automatically make wellbeing data risk-free or exempt a project from ethics requirements. Before inviting real participants, confirm the approved purpose, consent wording, access controls, retention period, deletion process, recruitment method, and whether institutional ethics review is required.

## Interpretation

The dashboard presents descriptive self-report results. Before and after changes do not prove that KōreroPal caused an improvement and should not be described as treatment effectiveness.

## Access limits

There is no public project-wide results page. Database reads require a valid recovery code and filter to that record. Supabase tables have RLS enabled with no public policies; the server uses a private secret key. This means the application server, not Supabase user authentication, enforces recovery-code access. The dashboard returns up to the latest 5,000 records per table when using Supabase.

Chat is limited to 2,000 characters per message, eight recent messages in the AI context, and 30 normal turns per reflection. Each submitted turn is processed once within its active session and automatic provider retries are disabled. A three-second pause limits rapid normal submissions. Crisis responses bypass the cooldown and turn limit. These are session-level controls, not a global abuse-prevention system.

KōreroPal does not currently provide self-service deletion. The project owner must establish a retention and deletion process before recruiting participants. Chat processing by Groq is separate from storage in the KōreroPal database.
