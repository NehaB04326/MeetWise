import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))

def send_action_dm(slack_id, task, deadline, item_id, base_url):
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*New Action Item from meeting*\n> {task}\n📅 Deadline: {deadline or 'Not set'}"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "✅ Mark Complete"},
                    "style": "primary",
                    "value": str(item_id),
                    "action_id": "mark_complete"
                }
            ]
        }
    ]
    try:
        response = client.chat_postMessage(channel=slack_id, blocks=blocks, text=f"Action: {task}")
        return response["ok"]
    except SlackApiError as e:
        print(f"Slack error: {e.response['error']}")
        return False

def send_weekly_report(channel_id, total, completed, pending_by_person):
    percent = round(completed / total * 100) if total > 0 else 0
    text = f"📊 *Weekly Action Report*\nTotal actions last 7 days: {total}\nCompleted: {completed} ({percent}%)\n\n*Pending by person:*\n"
    for row in pending_by_person:
        text += f"• {row['person_raw']}: {row['cnt']} pending\n"
    try:
        client.chat_postMessage(channel=channel_id, text=text)
    except SlackApiError as e:
        print(f"Weekly report error: {e}")