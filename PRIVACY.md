# KōreroPal privacy and data note

## Purpose

KōreroPal collects pseudonymous Likert ratings to examine changes in self-reported mood, stress, and energy and to describe how users rate the AI companion over repeated sessions.

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

The breathing timer runs in an embedded browser component, makes no external network requests and stores no breathing or health data. It pauses when the browser hides the page.

The contact form prepares a public GitHub issue link. Nothing is submitted until the user opens GitHub, reviews the report and submits it there. Reports must not contain private or wellbeing information. If configured, the newsletter link opens an external subscription service with its own privacy and consent controls; KōreroPal does not collect subscriber addresses itself.

Streamlit usage telemetry is disabled. The project adds no advertising scripts or optional analytics cookies. Necessary hosting, session and security mechanisms may still process connection data.

## External services

When AI mode is active, Groq receives the current message, up to eight previous messages from the active session, and up to three recent anonymous check-ins, including their timestamps and ratings. The anonymous study code is not included in the AI prompt. Groq processes this information to generate a response.

Streamlit hosts the application and Supabase hosts the anonymous rating tables. These providers may process technical or operational metadata under their own terms. Users should not enter identifying or highly private information into the chat.

## Research and ethics note

Removing direct identifiers does not automatically make wellbeing data risk-free or exempt a project from ethics requirements. Before inviting real participants, confirm the approved purpose, consent wording, access controls, retention period, deletion process, recruitment method, and whether institutional ethics review is required.

## Interpretation

The dashboard presents descriptive self-report results. Before and after changes do not prove that KōreroPal caused an improvement and should not be described as treatment effectiveness.

## Retention

Pseudonymous rating records are retained for 365 days. Local SQLite prunes records on application initialization. Supabase requires installation of the included scheduled cleanup SQL and verification of daily job success. A code holder can delete linked ratings at any time; any person possessing the code can also view or delete the data.

## Access limits

There is no public project-wide results page. Database reads require a valid recovery code and filter to that record. Supabase tables have RLS enabled with no public policies; the server uses a private secret key. This means the application server, not Supabase user authentication, enforces recovery-code access. The dashboard returns up to the latest 5,000 records per table when using Supabase.

Chat is limited to 2,000 characters per message, eight previous messages in the AI context, and 100 normal turns per reflection. Each submitted turn is processed once within its active session and automatic provider retries are disabled. A three-second pause limits rapid normal submissions. Crisis responses bypass the cooldown and turn limit. AI calls are additionally limited per session, per HMAC-hashed IP and globally using atomic server-side counters. Streamlit client IPs can be spoofed and shared gateways share a quota. If quota verification is unavailable, AI requests are blocked while built-in prompts and crisis resources remain available. Rate-limit keys contain no raw IPs and expire within two days.

Users can delete saved check-ins and evaluation ratings from Your progress using their recovery code. Ratings retention is 365 days, with hosted scheduled pruning described in the deployment documentation. Previously downloaded files and provider-held records are outside this deletion.
