import streamlit as st
import os
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Import your existing modules
from gpt_extractor import extract_action_items
from meeting_scoring import compute_meeting_score
from slack_client import send_action_dm  # we'll modify this to send plain message

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(page_title="Meeting Action Tracker", page_icon="🎯", layout="wide")

# Title and description
st.title("🎯 Meeting Action Intelligence Platform")
st.markdown("Upload a meeting transcript – AI extracts action items, assigns owners, calculates meeting effectiveness, and sends Slack reminders.")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    st.info("Make sure your `.env` file contains `GROQ_API_KEY`, `SLACK_BOT_TOKEN`, and `BASE_URL` (if using Slack).")
    if not os.getenv("GROQ_API_KEY"):
        st.error("GROQ_API_KEY not found. Please set it in .env")
    if not os.getenv("SLACK_BOT_TOKEN"):
        st.warning("SLACK_BOT_TOKEN not set – Slack notifications disabled.")

# Main input area
col1, col2 = st.columns([2, 1])
with col1:
    meeting_name = st.text_input("Meeting name", value="Sprint Planning")
    transcript = st.text_area("Paste meeting transcript", height=250, 
                              placeholder="Example:\nJohn: I'll fix the login bug by tomorrow.\nSarah: Update the docs by Friday.")
    uploaded_file = st.file_uploader("Or upload a .txt file", type=["txt"])

with col2:
    duration = st.number_input("Meeting duration (minutes)", min_value=0, value=45, step=5)
    process_button = st.button("🚀 Process Transcript", type="primary", use_container_width=True)

# Process when button clicked
if process_button:
    if uploaded_file is not None:
        transcript = uploaded_file.read().decode("utf-8")
    if not transcript.strip():
        st.error("Please provide a transcript (paste or upload).")
        st.stop()
    
    with st.spinner("AI is extracting action items and calculating score..."):
        # Extract action items using Groq
        items = extract_action_items(transcript, meeting_name)
        
        if not items:
            st.error("No action items extracted. Please check the transcript format.")
            st.stop()
        
        # Compute meeting score
        score_result = compute_meeting_score(transcript, items, duration)
        
        # Display action items in a nice table
        st.subheader("📋 Extracted Action Items")
        df = pd.DataFrame(items)
        # Rename columns for display
        if not df.empty:
            df = df.rename(columns={"task": "Task", "person": "Owner", "deadline": "Deadline"})
            st.dataframe(df, use_container_width=True)
        
        # Display meeting score with a gauge
        st.subheader("📊 Meeting Effectiveness Score")
        score = score_result["score"]
        breakdown = score_result["breakdown"]
        
        # Create columns for metric and details
        col_a, col_b = st.columns([1, 2])
        with col_a:
            # Show score with big font
            st.markdown(f"<h1 style='text-align: center; color: {'green' if score>=70 else 'orange' if score>=50 else 'red'};'>{score}/100</h1>", unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""
            - **Decisions:** {breakdown['decisions']} (score: {breakdown['decision_score']} pts)
            - **Items with owner:** {breakdown['items_with_owner']}/{breakdown['total_items']} ({breakdown['owner_score']} pts)
            - **Items with deadline:** {breakdown['items_with_deadline']}/{breakdown['total_items']} ({breakdown['deadline_score']} pts)
            - **Duration penalty:** {breakdown['duration_penalty']} pts
            """)
        
        # Send Slack notifications
        st.subheader("📬 Slack Notifications")
        if os.getenv("SLACK_BOT_TOKEN"):
            slack_sent = 0
            for item in items:
                task = item.get("task")
                person = item.get("person", "unassigned")
                if person.lower() != "unassigned":
                    # We need to resolve slack_id – reuse your resolve_slack_id function
                    from database import get_name_mapping  # or a simpler mapping
                    # For simplicity, we'll just log that we would send.
                    # In practice, you need to map person name to Slack user ID.
                    # For demo, you can map all to your own ID.
                    st.info(f"📨 Would send DM to {person} for task: {task}")
                    # Uncomment below when you have proper mapping
                    # slack_id = resolve_slack_id(person)
                    # if slack_id:
                    #     send_action_dm(slack_id, task, item.get("deadline"))
                    #     slack_sent += 1
            st.success(f"✅ Slack notifications sent to {slack_sent} assignees.")
        else:
            st.warning("Slack bot token missing. Skipping notifications.")
        
        # Optionally save to database – omitted for brevity

# Footer
st.markdown("---")
st.caption("Powered by Groq LLM and Slack API")