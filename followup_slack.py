import os
import json
import requests
from slack_sdk import WebClient

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
SLACK_TOKEN = os.getenv("SLACK_BOT_TOKEN")
client = WebClient(token=SLACK_TOKEN)

def extract_followup_details(transcript_text, meeting_name):
    prompt = f"""
You are given a meeting transcript. Identify if there is a proposed **follow-up meeting** (phrases like "let's meet again", "follow up next week", "schedule a call on...", "we'll reconvene on...").
If yes, extract:
- Proposed date and time (natural language, e.g., "June 2 at 10 AM")
- List of attendee names (extract names like John, Sarah, Alex)
- Suggested meeting title (e.g., "Follow-up on {meeting_name}")

Output ONLY valid JSON with keys: "has_followup" (boolean), "datetime" (string or null), "attendees" (list of strings), "title" (string).

Transcript:
{transcript_text[:2000]}
"""
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 300
    }
    response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
    if response.status_code != 200:
        return {"has_followup": False}
    content = response.json()["choices"][0]["message"]["content"].strip()
    # Clean markdown
    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
    result = json.loads(content)
    return result

def send_followup_slack(meeting_name, datetime_str, attendees, title):
    # You can choose a channel – use your weekly report channel or a new one
    channel = os.getenv("CHANNEL_ID_FOR_REPORT", "#general")
    attendees_text = ", ".join(attendees) if attendees else "the team"
    message = f"📅 *Follow-up Meeting Suggestion*\n" \
              f"*From meeting:* {meeting_name}\n" \
              f"*Title:* {title}\n" \
              f"*Proposed time:* {datetime_str}\n" \
              f"*Attendees:* {attendees_text}\n" \
              f"Please coordinate to schedule this meeting."
    try:
        client.chat_postMessage(channel=channel, text=message)
        return True
    except Exception as e:
        print(f"Slack error: {e}")
        return False