import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, request, render_template, jsonify, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from thefuzz import process
import secrets

from database import init_db, add_action_item, mark_completed
from database import save_meeting_score, get_all_meeting_scores
from gpt_extractor import extract_action_items
from slack_client import send_action_dm
from meeting_scoring import compute_meeting_score

# ------------------------------------------------------------
# Auto‑populate name_mapping from environment variable (if table is empty)
def populate_default_mapping():
    from database import get_db
    default_mapping_json = os.getenv("DEFAULT_SLACK_MAPPING", "{}")
    try:
        default_mapping = json.loads(default_mapping_json)
    except json.JSONDecodeError:
        print("Warning: DEFAULT_SLACK_MAPPING is not valid JSON. Skipping auto‑population.")
        return
    if not default_mapping:
        return
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM name_mapping").fetchone()[0]
        if count == 0:
            for raw_name, slack_id in default_mapping.items():
                conn.execute(
                    "INSERT OR IGNORE INTO name_mapping (raw_name, slack_id) VALUES (?, ?)",
                    (raw_name, slack_id)
                )
            print(f"Inserted {len(default_mapping)} default Slack user mapping(s).")
# ------------------------------------------------------------

init_db()
populate_default_mapping()

app = Flask(__name__)

# ------------------ AUTH SETUP ------------------
app.secret_key = os.getenv("SECRET_KEY", secrets.token_hex(32))

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to access this page."

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == 'demo':
        return User(user_id)
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        correct_password = os.getenv('AUTH_PASSWORD', 'demo123')
        if password == correct_password:
            user = User('demo')
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
# -------------------------------------------------

logging.basicConfig(level=logging.INFO)

def get_name_mapping():
    from database import get_db
    with get_db() as conn:
        rows = conn.execute("SELECT raw_name, slack_id FROM name_mapping").fetchall()
        return {row['raw_name']: row['slack_id'] for row in rows}

def resolve_slack_id(person_raw):
    mapping = get_name_mapping()
    if not mapping:
        return None
    lower_person = person_raw.lower()
    for key, sid in mapping.items():
        if key.lower() == lower_person:
            return sid
    best_match = process.extractOne(person_raw, mapping.keys(), score_cutoff=70)
    if best_match:
        return mapping[best_match[0]]
    return None

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        return redirect(url_for('index'))
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
@login_required
def upload_transcript():
    meeting_name = request.form.get("meeting_name", "Untitled Meeting")
    transcript = request.form.get("transcript") or request.files.get("file").read().decode("utf-8") if "file" in request.files else ""
    if not transcript:
        return jsonify({"error": "No transcript provided"}), 400

    items = extract_action_items(transcript, meeting_name)
    if not items:
        return jsonify({"error": "No action items extracted"}), 400

    duration_str = request.form.get("duration", "")
    duration_minutes = int(duration_str) if duration_str.isdigit() else None
    score_result = compute_meeting_score(transcript, items, duration_minutes)
    save_meeting_score(meeting_name, transcript[:500], score_result["score"], score_result["breakdown"])

    saved = []
    for item in items:
        task = item.get("task")
        person_raw = item.get("person", "unassigned")
        deadline = item.get("deadline")
        slack_id = resolve_slack_id(person_raw) if person_raw != "unassigned" else None
        item_id = add_action_item(meeting_name, task, person_raw, slack_id, deadline)
        saved.append({"id": item_id, "task": task, "person": person_raw, "deadline": deadline, "slack_id": slack_id})
        if slack_id:
            base_url = os.getenv("BASE_URL", request.host_url.rstrip('/'))
            send_action_dm(slack_id, task, deadline, item_id, base_url)

    return jsonify({
        "message": f"Extracted {len(saved)} action items",
        "items": saved,
        "score": score_result["score"],
        "score_breakdown": score_result["breakdown"]
    })

@app.route("/slack/interactive", methods=["POST"])
def slack_interactive():
    payload = request.form.get("payload")
    if not payload:
        return "No payload", 400
    import json
    data = json.loads(payload)
    if data["type"] == "block_actions":
        action = data["actions"][0]
        if action["action_id"] == "mark_complete":
            item_id = int(action["value"])
            mark_completed(item_id)
            return "", 200
    return "", 200

@app.route("/benchmark", methods=["GET"])
@login_required
def benchmark():
    scores = get_all_meeting_scores(20)
    data = [{"date": row["created_at"], "score": row["score"], "meeting": row["meeting_name"]} for row in scores]
    return jsonify(data)

@app.route("/health")
def health():
    return "OK", 200

if __name__ == "__main__":
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        from scheduler_jobs import scheduler
        scheduler.start()
        print("Scheduler started")
    app.run(debug=True, port=5000)
