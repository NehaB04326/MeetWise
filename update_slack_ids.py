import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
db_path = os.getenv("DATABASE_PATH", "actions.db")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()



real_slack_ids = {
    "john":  "U0B6Q9E58UQ",  
    "sarah": "U0B5WH22TT8", 
    "alex":  "U04YOUR_ALEX_ID"   
}

for raw_name, slack_id in real_slack_ids.items():
    cursor.execute(
        "UPDATE name_mapping SET slack_id = ? WHERE raw_name = ?",
        (slack_id, raw_name)
    )
    print(f"Updated {raw_name} -> {slack_id}")

conn.commit()
conn.close()
print("\n All Slack IDs updated successfully!")
