from apscheduler.schedulers.background import BackgroundScheduler
from database import get_stats_for_week
from slack_client import send_weekly_report
import os

def job_weekly_report():
    total, completed, pending = get_stats_for_week()
    channel = os.getenv("CHANNEL_ID_FOR_REPORT")
    if channel:
        send_weekly_report(channel, total, completed, pending)
    else:
        print("No CHANNEL_ID_FOR_REPORT set, skipping weekly report")

scheduler = BackgroundScheduler()
scheduler.add_job(func=job_weekly_report, trigger="cron", day_of_week="mon", hour=9, minute=0)
