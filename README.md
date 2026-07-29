# KōreroPal

KōreroPal is a wellbeing reflection app I built using Python and Streamlit, bringing together the two main areas I am studying, Computer Science and Psychology. I have always been interested in where technology and psychology overlap, particularly whether technology can support real human connection rather than attempting to replace it. This project became my way of exploring that question through something which actually works, rather than only writing about the idea.

The main purpose of KōreroPal is to give someone a place to check in with how they are feeling, talk through what is going on, and decide on one smaller step they can take afterwards. It is not trying to solve somebody's life through one AI response. A person may know they are stressed, exhausted or avoiding something, but knowing that does not automatically make it easy to decide what to do next. The app is built around that gap.

It began as a much smaller university portfolio project. The first version was mostly a Streamlit interface, a few ratings and a basic AI response. Once I got that working I kept finding more parts which needed to exist for it to feel like a proper application. Previous check-ins had to be stored somewhere. The user needed a way to return without making an account. The AI needed context but could not be given unlimited personal information. Errors needed to be dealt with properly, and the app still needed to function when Groq or Supabase stopped working.

What seemed like a simple reflection app quickly turned into a much larger project involving databases, APIs, privacy decisions, testing, deployment and a considerable amount of troubleshooting.

KōreroPal is still a student-built wellbeing tool. It is not a therapist, counsellor, doctor or diagnostic system. In an emergency in New Zealand call 111, or call or text 1737 to speak with a trained counsellor.

## Why I built it this way

A lot of applications immediately ask a person to create an account, enter an email, choose a password and hand over information before they have even used it. I considered adding normal accounts because it would have made returning users much easier to manage, although it also felt unnecessary for what I was trying to create. Somebody should be able to open the app and begin a check-in without creating another login, particularly when the subject they want to talk about may already feel personal.

Instead, KōreroPal creates a random anonymous code and places it in the URL. The person can bookmark that link and return to their previous ratings. No name, email address, password, phone number or student ID is required.

The session begins with three ratings: mood, stress and energy. The person can then speak with the reflection companion, look through some practical coping strategies, write a small next step and complete another rating afterwards.

I wanted the next step to stay small because broad advice is often easy to agree with and difficult to actually follow. “Improve your sleep” may be correct, but it is not particularly useful at 11:30 at night when someone is overwhelmed. Putting the phone away for ten minutes, preparing something for tomorrow or messaging one trusted person is at least something which can be done.

The question became; how much should the app remember?

I originally considered saving full chat histories so somebody could return to an older conversation. That would have been useful, but it would also mean storing a large amount of personal information which the app does not actually need. People could potentially write about relationships, family problems, university stress, health or anything else happening in their life.

I decided not to store conversations at all. The same applies to written goals, journal-style entries and AI responses. Giving up that history removes some functionality, but I think it better matches the purpose of the project. The app remembers the ratings needed to show patterns. It does not need to remember everything a person says.

## The original KōreroMate name

The project was originally called KōreroMate.

I chose the name because I was reading “mate” completely in the English sense, as someone friendly you could talk to. It sounded like a good name for the idea and I thought it fitted the application well. I had already used KōreroMate throughout the interface, code, database, documentation, deployment setup and repository files.

I was very close to the first full release with that name.

It was only when I spoke to someone about the project that they pointed out something I had completely missed. People could read *mate* as the Māori word rather than the English word, where it can be associated with sickness, death or somebody being dead.

This meant the name of my New Zealand wellbeing application could be interpreted as something close to “speak to the dead”.

That was almost the complete opposite of what I was trying to create.

It is not necessarily the exact grammatical translation, but the association was strong enough that keeping the name would have been careless. It was honestly quite embarrassing because I had spent so long building the entire application around the name without checking something that important. I had only thought about whether it sounded friendly in English and had not properly considered how the Māori word beside it could be understood.

I changed the project to KōreroPal before release. This meant going back through almost everything I had already completed, including the visible branding, anonymous user codes, database filenames, documentation, Streamlit settings, links and planned GitHub repository name.

This became one of the most important lessons from the whole project. A name is not only a small branding choice, particularly when te reo Māori is being used in a wellbeing application made in New Zealand. If I started the project again, I would check the cultural meaning and possible interpretation of the name before writing the rest of the application around it, rather than discovering the problem when I was nearly ready to publish.

## What changed while I was building it

The AI model changed several times.

The earlier version used `llama-3.1-8b-instant`. It was useful for getting the first working version together because it was fast and relatively easy to use, but I found it would sometimes repeat phrases, ignore parts of the prompt or move too quickly into generic advice.

I later changed it to `llama-3.3-70b-versatile`. The larger model is much better at following the reflection instructions and keeping track of what has already been said. It is also better at asking a useful question rather than immediately producing a large list of suggestions.

Changing the model did not fix everything. I rewrote the prompt several times because the earlier versions either gave too much advice, sounded unnaturally supportive, or acted as though every problem could be solved through one conversation. The final prompt places more emphasis on reflection, asking questions, keeping responses realistic and helping the user decide on a smaller next step.

I expected the AI integration to be the hardest part.

It was not.

Most of the time ended up going into configuration, databases, handling failures and making sure one broken service did not bring down the entire app. I underestimated how much time I would spend fixing setup problems compared with actually adding new features.

Supabase caused several different problems during development. At one point check-ins were not being saved properly. Later, the app was expecting database tables which had not been correctly created. More recently the Supabase project hostname itself stopped resolving, which produced a large DNS connection error inside the app.

I was initially treating everything as one database problem when there were actually different problems happening at different stages. Fixing the project URL would not fix a missing table, and creating the table would not fix a DNS failure. I probably spent much longer than I should have trying changes which were unrelated to the actual problem.

The original error handling was also terrible for an actual user. The page could show a full Python exception containing the Supabase URL, REST request path, connection details and technical DNS message. That might help me while debugging, but it means nothing to somebody trying to complete a wellbeing check-in.

KōreroPal now catches problems such as incorrect project URLs, DNS failures, timeouts, invalid keys, unavailable projects and missing tables. The user gets a normal explanation while the technical exception stays out of the interface.

I also changed my mind about how dependent the app should be on Groq. My first thinking was that if the project used an AI model, then the AI service was simply required. That made the entire reflection section dependent on one external API and one working key.

That was not a great design.

KōreroPal now includes a smaller built-in response system which looks for certain themes in the user's message and gives a basic reflection response without contacting Groq. It is much more limited than the full model. Still, the app remains usable instead of ending the session with another error.

If I rebuilt the project from the beginning, I would separate the database, interface and external service code much earlier. At first, keeping things close together was quicker because I was experimenting and wanted to see features working. As the application grew it became harder to change one section without affecting another.

I would also design the configuration and error handling before deployment, not after something breaks. That is much easier to say now.

## Data and privacy

The application stores:

* The anonymous user code
* Check-in timestamps
* Mood ratings
* Stress ratings
* Energy ratings
* Before and after session ratings
* Three short numerical feedback ratings about the reflection companion

It does not store:

* Names
* Email addresses
* Phone numbers
* Passwords
* Student IDs
* Chat messages
* AI responses
* Journal writing
* Written goals

Messages remain inside the active Streamlit session and disappear when that session ends.

When Groq is used, it receives the current message, a limited amount of recent conversation from the same session, and up to three recent anonymous check-ins. The anonymous user code is not sent to Groq.

I wanted the AI to have enough context to avoid responding as though every message exists on its own, without sending an entire history or information which has no reason to leave the app.

The complete data explanation is inside [`PRIVACY.md`](PRIVACY.md).

## Local and deployed databases

KōreroPal uses SQLite while running locally. This made development easier because I could work on the app, save test check-ins and run database tests without needing Supabase to be available every time.

The deployed version can use Supabase. The SQL for the required tables is included in [`supabase_schema.sql`](supabase_schema.sql).

Using both databases created extra work because they needed to behave in a similar way, but it made the project much easier to develop and test. It also means a local copy of the project is not useless without internet access or a configured Supabase project.

## Open the project in VS Code

Extract the project folder first. Do not open the ZIP file directly.

Open VS Code, select **File → Open Folder**, and choose the `KoreroPal` folder.

You can also open the folder from a terminal if the VS Code command-line tool is installed:

```bash
cd /path/to/KoreroPal
code .
```

Install the official **Python** extension from Microsoft if VS Code asks for it.

## Create the Python environment

KōreroPal is set up for Python 3.12.

### macOS or Linux

Open the VS Code terminal through **Terminal → New Terminal**, then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows PowerShell

Open the VS Code terminal and run:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If PowerShell blocks the activation script, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

## Select the interpreter in VS Code

After creating the virtual environment:

1. Press `Command + Shift + P` on macOS or `Ctrl + Shift + P` on Windows.
2. Search for `Python: Select Interpreter`.
3. Choose the interpreter inside `.venv`.

It should look similar to:

```text
.venv/bin/python
```

on macOS or Linux, or:

```text
.venv\Scripts\python.exe
```

on Windows.

## Run KōreroPal

Make sure the virtual environment is active, then run:

```bash
python -m streamlit run app.py
```

Using `python -m streamlit` makes sure VS Code runs Streamlit from the selected virtual environment instead of another Python installation.

The app should open automatically in the browser. If it does not, open:

```text
http://localhost:8501
```

The app can run locally without Groq or Supabase details. Without Groq it uses the built-in response system. Without Supabase it uses SQLite.

Stop the app by clicking inside the terminal and pressing:

```text
Control + C
```

## Keys and configuration

The example secrets file is located at:

```text
.streamlit/secrets.toml.example
```

### macOS or Linux

Create the real local secrets file with:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

### Windows PowerShell

Create it with:

```powershell
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Open `.streamlit/secrets.toml` in VS Code and add the Groq and Supabase details.

The real secrets file is excluded through `.gitignore` and should never be committed. This was another part of Git which I learned more about while preparing the project for release. Deleting a secret from the newest version does not remove it from earlier repository history.

Once a key has appeared publicly it should be revoked, not hidden through another commit and assumed to be safe.

More complete setup instructions are available in [`DEPLOYMENT.md`](DEPLOYMENT.md).

## Run the tests

Make sure the virtual environment is active, then run:

```bash
python -m pytest
```

There are currently 14 automated tests covering the local database, summaries, configuration, coping strategy selection and parts of the safety behaviour.

GitHub Actions is also configured to run the tests whenever code is pushed to the repository.

The testing section grew later in development. At the beginning I was mostly opening the app, clicking through each page and checking whether it appeared to work. This became less reliable as more database and configuration behaviour was added. Fixing one problem could quietly break another section which I had forgotten to manually check.

Automated tests are not enough to prove the entire app works perfectly, especially where an external AI response is involved, but they catch many of the predictable failures much faster than repeatedly testing everything by hand.

## Useful Git commands

Check which files have changed:

```bash
git status
```

View the changes before committing:

```bash
git diff
```

Add all project changes:

```bash
git add .
```

If the repository already contains the clean first commit and has not been pushed yet, update that commit with:

```bash
git commit --amend --no-edit
```

Check the commit history:

```bash
git log --oneline
```

Push the project for the first time:

```bash
git push -u origin main
```

## Current limitations

KōreroPal is working, but it is not finished in the sense that a commercial or clinical application would be finished.

The check-in system can show changes in somebody's own ratings, but it cannot prove KōreroPal caused those changes. A person may rate their mood higher after a session for many different reasons. The ratings are also subjective.

The AI can misunderstand what somebody means. Safety instructions, crisis wording and restricted prompts reduce some risk but cannot make a language model completely reliable. This is why I kept the app focused on reflection, coping ideas and a next step rather than attempting diagnosis or treatment.

The built-in fallback responses are intentionally basic. They allow the app to keep functioning, but they do not have the same understanding or flexibility as the full model.

Formal research would require much more than deploying the app and collecting ratings. It would need participant information, a proper consent process, a clear study design, decisions around data retention and ethics approval where required.

## Final thoughts

KōreroPal is mainly a portfolio project, but it is also something I care about beyond showing that I can write Python.

It represents the direction I am interested in going towards; technology which understands its limits, supports people without collecting everything about them, and helps human connection rather than attempting to replace it.

The project taught me far more through the things which broke, the decisions I changed and the parts I originally underestimated than it would have if the first version had simply worked. Even the name nearly made it to release while accidentally sounding like an app for speaking to the dead. That is not a mistake I am likely to make again.
