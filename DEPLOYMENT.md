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

- the sidebar shows `AI service active`
- the sidebar shows `Data storage: Supabase`
- a daily check-in saves successfully
- the anonymous dashboard reloads the saved check-in
- the AI chat responds and the evaluation saves
- the project results page loads without exposing study codes
- the GitHub Actions test workflow passes

## Official documentation

- Streamlit deployment: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Streamlit secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- Supabase API keys: https://supabase.com/docs/guides/getting-started/api-keys
- Supabase Data REST API: https://supabase.com/docs/guides/api
- Groq supported models: https://console.groq.com/docs/models
- KōreroPal repository: https://github.com/nfal707/KoreroPal
