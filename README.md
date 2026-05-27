**MeetWise**

**What MeetWise does:**

- Extracts action items (task, owner, deadline) from meeting transcripts using Groq LLM (Llama 3.3), including Hinglish (Hindi+English mixed) support.
- Sends interactive Slack direct messages with “Mark Complete” buttons; updates task status in SQLite on button click.
- Calculates a meeting effectiveness score (0‑100) based on decisions, owner assignment, deadlines, and meeting duration.
- Automatically maps extracted names to real Slack user IDs using case‑insensitive and fuzzy matching.
- Generates weekly team reports (pending/completed actions) posted to a Slack channel via APScheduler.
- Provides a password‑protected web dashboard with session‑based authentication (Flask‑Login).
- Persists all data (action items, name mappings, scores) using SQLite with a persistent disk for deployments.

**Tech Stack**
**Backend:** Python, Flask, Flask‑Login, Gunicorn

**AI / LLM:** Groq API (Llama 3.3‑70B) – free tier, Hinglish‑aware prompting

**Database:** SQLite (persistent disk on Render)

**Messaging:** Slack API (Bot Token, interactive webhooks, chat.postMessage)

**Scheduling:** APScheduler (weekly reports)

**Frontend:** HTML5, CSS (Flexbox/Grid), vanilla JavaScript

**Deployment:** Render (free tier, environment variables, persistent disk)

**Authentication:** Session‑based (Flask‑Login)

**Utilities:** python‑dotenv, requests, thefuzz (fuzzy matching), pytz

<img width="4746" height="2781" alt="deepseek_mermaid_20260527_622f63" src="https://github.com/user-attachments/assets/2a343bad-9a08-4213-bc65-e4d89b3489bb" />

**Live Link:**
https://meetwise-etk7.onrender.com

