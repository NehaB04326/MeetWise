# gpt_extractor.py - Hinglish‑aware version using requests (no Groq SDK)
import os
import json
import requests
from datetime import datetime, timedelta

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

def extract_action_items(transcript_text, meeting_name="General"):
    # Get today's date for relative deadline calculation
    today = datetime.today().date()
    tomorrow = today + timedelta(days=1)
    
    prompt = f"""
You are given a meeting transcript that may be in **Hinglish** – Hindi written using the English (Latin) script, often mixed with English words. 
Extract all action items as a JSON list of objects with exactly these keys: "task", "person", "deadline".

Instructions:
- "task": A clear, concise description of what needs to be done. **Translate Hinglish/Hindi parts to English**.
- "person": The name of the person responsible (as spoken, e.g., "John", "Rahul", "Priya", or "me"). 
  If the speaker says "main karunga" (I will do it), use the speaker's name if available, otherwise use "unassigned".
- "deadline": Convert to YYYY-MM-DD format.
  - For words like "kal" → use {tomorrow}
  - "parso" (day after tomorrow) → {today + timedelta(days=2)}
  - "aaj" (today) → {today}
  - "Friday", "next week", etc. → compute appropriately.
  - If no deadline mentioned, set to null.
- If multiple people are mentioned, pick the primary owner.
- If no person is clearly responsible, set "person" to "unassigned".

Respond **ONLY** with valid JSON, no extra explanation or markdown.

Example Hinglish input:
"Rahul: me ye login bug kal tak fix kar dunga."
Output:
[{{"task": "fix login bug", "person": "Rahul", "deadline": "{tomorrow}"}}]

Now process this transcript:

{transcript_text}
"""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",  # good multilingual support
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 800
    }
    try:
        response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
        if response.status_code != 200:
            print(f"Groq API error: {response.text}")
            return []
        content = response.json()["choices"][0]["message"]["content"].strip()
        # Remove markdown code fences if present
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        items = json.loads(content)
        # Ensure each item has the required keys
        for item in items:
            item.setdefault("person", "unassigned")
            item.setdefault("deadline", None)
        return items
    except Exception as e:
        print(f"Extraction error: {e}")
        return []