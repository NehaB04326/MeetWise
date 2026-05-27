import re
from datetime import datetime

def compute_meeting_score(transcript, extracted_items, duration_minutes=None):
    """
    Calculate a meeting effectiveness score (0-100).
    - decisions: count of 'decision' or 'agreed' keywords
    - action_items: quality of items (owner, deadline)
    - duration penalty if over 60 min
    """
    # 1. Decisions (rough keyword count)
    decisions = transcript.lower().count("decision") + transcript.lower().count("agreed")
    decision_score = min(decisions * 10, 30)   # max 30 points
    
    # 2. Action item quality
    total_items = len(extracted_items)
    items_with_owner = sum(1 for i in extracted_items if i.get('person') and i.get('person') != 'unassigned')
    items_with_deadline = sum(1 for i in extracted_items if i.get('deadline'))
    
    owner_score = (items_with_owner / max(total_items, 1)) * 25   # max 25
    deadline_score = (items_with_deadline / max(total_items, 1)) * 25   # max 25
    item_count_score = min(total_items * 5, 20)   # max 20
    
    # 3. Duration penalty
    duration_penalty = 0
    if duration_minutes:
        if duration_minutes > 90:
            duration_penalty = 20
        elif duration_minutes > 60:
            duration_penalty = 10
    
    raw_score = decision_score + owner_score + deadline_score + item_count_score - duration_penalty
    score = max(0, min(100, round(raw_score)))
    
    return {
        "score": score,
        "breakdown": {
            "decisions": decisions,
            "decision_score": decision_score,
            "total_items": total_items,
            "items_with_owner": items_with_owner,
            "items_with_deadline": items_with_deadline,
            "owner_score": round(owner_score, 1),
            "deadline_score": round(deadline_score, 1),
            "item_count_score": item_count_score,
            "duration_penalty": duration_penalty
        }
    }