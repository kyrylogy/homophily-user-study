"""
CSV-based Storage for Homophily Study
Simple CSV files - easy to analyze in Excel/Python/R.
"""

import csv
import os
import json
from datetime import datetime
from pathlib import Path
import config

# Data directory
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# CSV files
PARTICIPANTS_FILE = DATA_DIR / "participants.csv"
MESSAGES_FILE = DATA_DIR / "messages.csv"
RATINGS_FILE = DATA_DIR / "ratings.csv"

# CSV Headers
PARTICIPANTS_HEADERS = [
    "id", "created_at", "completed_at",
    # Counterbalancing assignment
    "group",           # A or B (counterbalance order)
    "is_outlier",      # true if Low E/Low A (assignment flipped)
    # Demographics
    "age", "gender", "education",
    # TIPI scores
    "tipi_1", "tipi_2", "tipi_3", "tipi_4", "tipi_5",
    "tipi_6", "tipi_7", "tipi_8", "tipi_9", "tipi_10",
    # Computed Big Five
    "extraversion", "agreeableness", "conscientiousness", "neuroticism", "openness",
    # Other
    "interests", "communication_style",
    # Final comparison
    "preferred_bot", "preference_reason"
]

MESSAGES_HEADERS = [
    "participant_id", "phase", "role", "content", "bot_type", "topic", "model", "created_at"
]

RATINGS_HEADERS = [
    "participant_id", "phase", "bot_type", "topic",
    "trust", "likability", "similarity", "naturalness", "satisfaction", 
    "open_response", "created_at"
]


def _init_csv(filepath: Path, headers: list):
    """Create CSV with headers if it doesn't exist."""
    if not filepath.exists():
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)


def init_db():
    """Initialize CSV files."""
    _init_csv(PARTICIPANTS_FILE, PARTICIPANTS_HEADERS)
    _init_csv(MESSAGES_FILE, MESSAGES_HEADERS)
    _init_csv(RATINGS_FILE, RATINGS_HEADERS)


def _append_row(filepath: Path, row: list):
    """Append a row to CSV."""
    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(row)


def create_participant(participant_id: str, group: str) -> str:
    """Create a new participant with counterbalance group assignment."""
    row = [participant_id, datetime.now().isoformat(), ""]  # id, created_at, completed_at
    row.append(group)  # group (A or B)
    row.extend([""] * (len(PARTICIPANTS_HEADERS) - 4))  # rest of fields
    _append_row(PARTICIPANTS_FILE, row)
    return participant_id


def get_participant_count() -> int:
    """Get total participant count for counterbalancing."""
    if not PARTICIPANTS_FILE.exists():
        return 0
    with open(PARTICIPANTS_FILE, 'r', newline='', encoding='utf-8') as f:
        return sum(1 for _ in f) - 1  # minus header


def calculate_big_five(tipi: dict) -> dict:
    """Calculate Big Five scores from TIPI responses.
    
    TIPI scoring (1-7 scale):
    Extraversion: 1, 6R
    Agreeableness: 2R, 7
    Conscientiousness: 3, 8R
    Neuroticism: 4, 9R
    Openness: 5, 10R
    
    R = reverse scored (8 - score)
    """
    def r(val): return 8 - val  # reverse score
    
    t = {k: int(v) for k, v in tipi.items() if k.startswith('tipi_')}
    
    return {
        'extraversion': (t.get('tipi_1', 4) + r(t.get('tipi_6', 4))) / 2,
        'agreeableness': (r(t.get('tipi_2', 4)) + t.get('tipi_7', 4)) / 2,
        'conscientiousness': (t.get('tipi_3', 4) + r(t.get('tipi_8', 4))) / 2,
        'neuroticism': (t.get('tipi_4', 4) + r(t.get('tipi_9', 4))) / 2,
        'openness': (t.get('tipi_5', 4) + r(t.get('tipi_10', 4))) / 2
    }


def is_outlier_profile(big_five: dict) -> bool:
    """Check if user is an outlier (Low E or Low A) - needs flipped assignment."""
    # Threshold: below 3.5 on 1-7 scale is considered "Low"
    return big_five['extraversion'] < 3.5 or big_five['agreeableness'] < 3.5


def save_profile(participant_id: str, profile: dict):
    """Save participant profile with computed Big Five scores."""
    # Calculate Big Five
    big_five = calculate_big_five(profile)
    is_outlier = is_outlier_profile(big_five)
    
    rows = []
    with open(PARTICIPANTS_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['id'] == participant_id:
                row.update({
                    'is_outlier': str(is_outlier).lower(),
                    'age': profile.get('age', ''),
                    'gender': profile.get('gender', ''),
                    'education': profile.get('education', ''),
                    'tipi_1': profile.get('tipi_1', ''),
                    'tipi_2': profile.get('tipi_2', ''),
                    'tipi_3': profile.get('tipi_3', ''),
                    'tipi_4': profile.get('tipi_4', ''),
                    'tipi_5': profile.get('tipi_5', ''),
                    'tipi_6': profile.get('tipi_6', ''),
                    'tipi_7': profile.get('tipi_7', ''),
                    'tipi_8': profile.get('tipi_8', ''),
                    'tipi_9': profile.get('tipi_9', ''),
                    'tipi_10': profile.get('tipi_10', ''),
                    'extraversion': f"{big_five['extraversion']:.2f}",
                    'agreeableness': f"{big_five['agreeableness']:.2f}",
                    'conscientiousness': f"{big_five['conscientiousness']:.2f}",
                    'neuroticism': f"{big_five['neuroticism']:.2f}",
                    'openness': f"{big_five['openness']:.2f}",
                    'interests': profile.get('interests', ''),
                    'communication_style': profile.get('communication_style', '')
                })
            rows.append(row)
    
    with open(PARTICIPANTS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=PARTICIPANTS_HEADERS)
        writer.writeheader()
        writer.writerows(rows)
    
    return {'is_outlier': is_outlier, 'big_five': big_five}


def get_participant(participant_id: str) -> dict:
    """Get participant data."""
    if not PARTICIPANTS_FILE.exists():
        return None
    with open(PARTICIPANTS_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['id'] == participant_id:
                return dict(row)
    return None


def save_message(participant_id: str, phase: int, role: str, content: str, 
                 bot_type: str = "", topic: str = "", model: str = ""):
    """Save a chat message with bot type and topic."""
    content_safe = content.replace('\n', '\\n').replace('\r', '')
    row = [participant_id, phase, role, content_safe, bot_type, topic, model, datetime.now().isoformat()]
    _append_row(MESSAGES_FILE, row)


def get_messages(participant_id: str, phase: int) -> list:
    """Get chat history for a phase."""
    messages = []
    if not MESSAGES_FILE.exists():
        return messages
        
    with open(MESSAGES_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['participant_id'] == participant_id and int(row['phase']) == phase:
                content = row['content'].replace('\\n', '\n')
                messages.append({"role": row['role'], "content": content})
    return messages


def get_message_count(participant_id: str, phase: int) -> int:
    """Get number of user messages in a phase."""
    count = 0
    if not MESSAGES_FILE.exists():
        return count
        
    with open(MESSAGES_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row['participant_id'] == participant_id and 
                int(row['phase']) == phase and 
                row['role'] == 'user'):
                count += 1
    return count


def save_rating(participant_id: str, phase: int, bot_type: str, topic: str, rating: dict):
    """Save bot rating with bot type and topic."""
    open_response = rating.get('open_response', '').replace('\n', '\\n').replace('\r', '')
    row = [
        participant_id, phase, bot_type, topic,
        rating.get('trust', ''),
        rating.get('likability', ''),
        rating.get('similarity', ''),
        rating.get('naturalness', ''),
        rating.get('satisfaction', ''),
        open_response,
        datetime.now().isoformat()
    ]
    _append_row(RATINGS_FILE, row)


def save_preference(participant_id: str, preferred_bot: str, reason: str):
    """Save final bot preference."""
    rows = []
    with open(PARTICIPANTS_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['id'] == participant_id:
                row['preferred_bot'] = preferred_bot
                row['preference_reason'] = reason.replace('\n', '\\n').replace('\r', '')
            rows.append(row)
    
    with open(PARTICIPANTS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=PARTICIPANTS_HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def mark_complete(participant_id: str):
    """Mark participant as completed."""
    rows = []
    with open(PARTICIPANTS_FILE, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['id'] == participant_id:
                row['completed_at'] = datetime.now().isoformat()
            rows.append(row)
    
    with open(PARTICIPANTS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=PARTICIPANTS_HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def export_data() -> dict:
    """Export all data as dict (for JSON download)."""
    data = {"exported_at": datetime.now().isoformat()}
    
    for name, filepath in [("participants", PARTICIPANTS_FILE), 
                           ("messages", MESSAGES_FILE), 
                           ("ratings", RATINGS_FILE)]:
        if filepath.exists():
            with open(filepath, 'r', newline='', encoding='utf-8') as f:
                data[name] = list(csv.DictReader(f))
        else:
            data[name] = []
    
    return data

