# KōreroPal deployment

## 1. Configure Supabase

Open the Supabase project and confirm it is active.

1. Open the SQL editor.
2. Run the complete contents of `supabase_schema.sql`.
3. Open the project API settings.
4. Copy the project URL exactly. It should look like `https://your-project-ref.supabase.co` and must not include `/rest/v1`.
5. Copy a server-side Supabase secret key. Do not place it in source code or GitHub.

## 2. Create the Streamlit app

In Streamlit Community Cloud:

1. Create a new app from `nfal707/KoreroPal`.
2. Select the `main` branch.
3. Set the main file path to `app.py`.
4. Open the app secrets and add:

```toml
GROQ_API_KEY = "groq_key"
GROQ_MODEL = "llama-3.3-70b-versatile"

SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_SECRET_KEY = "supabase_super_duper_secret_key"
```


## 3. Verify the deployment

Check all of the following:

- About this space shows `AI reflection configured`
- About this space shows `Ratings storage: Supabase`
- a daily check-in saves successfully
- the anonymous dashboard reloads the saved check-in
- the AI chat responds once per submission, End chat reveals final ratings, and the evaluation saves once
- each dashboard only shows the current recovery code’s ratings; there is no public aggregate results page
- the GitHub Actions test workflow passes

## Official documentation

- Streamlit deployment: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Streamlit secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- Supabase API keys: https://supabase.com/docs/guides/getting-started/api-keys
- Supabase Data REST API: https://supabase.com/docs/guides/api
- Groq supported models: https://console.groq.com/docs/models
- KōreroPal repository: https://github.com/nfal707/KoreroPal

## Reproducible local checks

Use Python 3.12, create `.venv`, then install `requirements-lock.txt` for the versions tested with this update. `requirements.txt` contains the direct pinned dependencies used by Streamlit Cloud. Run `python -m pytest` before publishing. Tests use temporary SQLite databases and mocked provider responses; they do not send chat data to Groq.

The current app uses Streamlit 1.66.1. Keep its CORS and XSRF protections enabled. No secret belongs in Git, URLs, logs, screenshots, or browser-side code. Modern Supabase secret keys are sent only in the `apikey` header; legacy service-role JWTs also use the Authorization header. Partially configured Supabase fails closed instead of silently writing to local SQLite.

The Supabase tables are intentionally server-only. Do not add public RLS policies to silence the informational no-policy notices. The schema script includes a conditional permission hardening step for the optional `rls_auto_enable` event-trigger function. The existing hosted KoreroPal project was checked and its unnecessary PUBLIC, anon, and authenticated execution grants were revoked on 24 October 2026. No rating data or table structure was changed.

Before opening this portfolio project to broader use, set provider spend limits and add host-level abuse controls. The app's cooldown and request IDs are scoped to one process/session and do not prevent someone opening multiple sessions. An interrupted network request cannot guarantee provider-level exactly-once billing. Automatic retries are disabled to avoid silently repeating requests.

Use a configured staging deployment to verify real Groq response quality and Supabase REST writes before merging to the live branch. A local fallback-mode preview does not verify live credentials or model availability. The included keyword safety checks and model instructions are limited safeguards, not a clinical safety certification.

Provider behaviour references: [Groq retries and timeouts](https://github.com/groq/groq-python#retries), [Supabase API keys](https://supabase.com/docs/guides/getting-started/api-keys), [Supabase function permissions](https://supabase.com/docs/guides/database/database-linter?lint=0028_anon_security_definer_function_executable).

## Website assets and optional services

Keep `server.enableStaticServing = true` in `.streamlit/config.toml`. Streamlit serves the two public files in `static/`: the transparent original logo and the woven SVG. Do not place private files in that folder. The Python code, database, source logo and secrets are outside the static directory. A configured `server.baseUrlPath` is included in asset URLs.

Optional secrets:

```toml
CONTACT_EMAIL = "your-verified-public-project-address@example.com"
NEWSLETTER_URL = "https://your-real-subscription-service.example/signup"
```

Leave these unset until real details are available. Email links are only shown for a valid address, and the newsletter section only appears for an HTTPS URL. The external signup provider must handle subscriber consent, preferences and unsubscribe. The built-in feedback form prepares a public issue draft for the existing repository; it never sends or stores reports automatically.

Check the breathing timer on desktop and mobile, journal navigation and clearing, resource search, and both the empty and populated rating views. Journal text and daily habits are session-only. Do not describe them as synced account data. See `DESIGN.md` for the visual system, source assets and Streamlit's publishing/SEO limits.
