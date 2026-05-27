# update_slack_ids.py
import sqlite3
import os
from dotenv import load_dotenv

# Load environment variables (so we use the correct database path)
load_dotenv()
db_path = os.getenv("DATABASE_PATH", "actions.db")

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 🔁 REPLACE THESE WITH YOUR REAL SLACK USER IDs
# To get a Slack User ID: 
#   - Open Slack desktop or web → click your profile picture → "Copy member ID"
#   - It looks like: U04ABCDEFG

real_slack_ids = {
    "john":  "U0B6Q9E58UQ",   # ← replace with actual ID for John
    "sarah": "U0B5WH22TT8",  # ← replace with actual ID for Sarah
    "alex":  "U04YOUR_ALEX_ID"    # ← replace with actual ID for Alex
}

# Update the name_mapping table
for raw_name, slack_id in real_slack_ids.items():
    cursor.execute(
        "UPDATE name_mapping SET slack_id = ? WHERE raw_name = ?",
        (slack_id, raw_name)
    )
    print(f"Updated {raw_name} -> {slack_id}")

# Commit changes and close
conn.commit()
conn.close()
print("\n✅ All Slack IDs updated successfully!")
