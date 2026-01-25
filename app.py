"""
Homophily Study - Main FastAPI Application
Modern, fast, clean - with streaming support.
Run with: uv run app.py
"""

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
import zipfile
import io
from openai import OpenAI
import uuid
import json
import random
import config
import database as db

app = FastAPI(title="Homophily study", description="AI Conversation Study Platform")

# Initialize
client = OpenAI(api_key=config.OPENAI_API_KEY)
db.init_db()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the main page."""
    with open("templates/index.html", "r") as f:
        return f.read()


@app.post("/api/start")
async def start_session():
    """Start a new participant session with counterbalance assignment."""
    participant_id = str(uuid.uuid4())[:8]
    
    # Counterbalancing: alternate between group A and B
    count = db.get_participant_count()
    group = "A" if count % 2 == 0 else "B"
    
    db.create_participant(participant_id, group)
    return {"participant_id": participant_id, "group": group}


@app.post("/api/profile")
async def save_profile(request: Request):
    """Save participant profile and return assignment."""
    data = await request.json()
    participant_id = data.get("participant_id")
    if not participant_id:
        raise HTTPException(400, "Missing participant_id")
    
    # Save profile and get personality analysis
    result = db.save_profile(participant_id, data.get("profile", {}))
    
    # Get participant's group assignment
    participant = db.get_participant(participant_id)
    group = participant.get('group', 'A')
    is_outlier = result['is_outlier']
    
    # Determine persona assignment via similarity to centroids (A, C, O)
    # Build participant vector p = [E, A, C, ES, O] where ES = emotional stability = 8 - neuroticism
    bf = result['big_five']
    try:
        p_e = float(bf.get('extraversion', 4.0))
        p_a = float(bf.get('agreeableness', 4.0))
        p_c = float(bf.get('conscientiousness', 4.0))
        p_n = float(bf.get('neuroticism', 4.0))
        p_o = float(bf.get('openness', 4.0))
    except Exception:
        p_e, p_a, p_c, p_n, p_o = 4.0, 4.0, 4.0, 4.0, 4.0

    p_vector = [p_e, p_a, p_c, (8.0 - p_n), p_o]

    # Compute similarity to each centroid
    best_label = None
    best_ss = -1.0
    similarities = {}
    # remove B from centroid consi
    for label, mu in config.CENTROIDS.items():
        # normalized mean absolute distance
        d = sum(abs(p_vector[j] - mu[j]) / 6.0 for j in range(5)) / 5.0
        ss = 1.0 - d
        similarities[label] = ss
        if ss > best_ss:
            best_ss = ss
            best_label = label


    persona = best_label 

    # persist assigned persona
    try:
        db.set_assigned_persona(participant_id, persona)
    except Exception:
        pass

    # Randomize bot order (one default, one persona) and randomize topic order
    topics = [config.TOPIC_A, config.TOPIC_B]
    random.shuffle(topics)

    # Decide whether chat1 is persona or default
    if random.random() < 0.5:
        chat1_bot = 'persona'
        chat2_bot = 'default'
    else:
        chat1_bot = 'default'
        chat2_bot = 'persona'

    chat1_topic = topics[0]
    chat2_topic = topics[1]
    
    # prepare persona trait vector for frontend (O, C, E, A, N)
    mu = config.CENTROIDS.get(persona, config.CENTROIDS['A'])

    # mu is [E, A, C, ES, O]
    persona_traits = {
        'Openness': float(mu[4]),
        'Conscientiousness': float(mu[2]),
        'Extroversion': float(mu[0]),
        'Agreeableness': float(mu[1]),
        'Neuroticism': float(8.0 - mu[3])
    }

    return {
        "status": "ok",
        "assignment": {
            "group": group,
            "is_outlier": is_outlier,
            "big_five": result['big_five'],
            "persona_label": persona,
            "persona_traits": persona_traits,
            "similarities": similarities,
            "chat1": {"bot_type": chat1_bot, "topic": chat1_topic},
            "chat2": {"bot_type": chat2_bot, "topic": chat2_topic}
        }
    }


@app.post("/api/chat")
async def chat(request: Request):
    """Send message and get bot response."""
    data = await request.json()
    participant_id = data.get("participant_id")
    phase = data.get("phase", 1)
    message = data.get("message", "").strip()
    
    if not participant_id or not message:
        raise HTTPException(400, "Missing participant_id or message")
    
    # Get bot type and topic from request
    bot_type = data.get("bot_type", "high_match")
    topic = data.get("topic", {})
    topic_title = topic.get("title", "general discussion")
    topic_id = topic.get("id", "unknown")
    
    # Save user message
    db.save_message(participant_id, phase, "user", message, bot_type, topic_id)
    
    # Get chat history
    history = db.get_messages(participant_id, phase)
    
    # Select prompt based on bot_type ('default' or 'persona') and assigned persona
    participant = db.get_participant(participant_id) or {}
    if bot_type == 'default':
        O = C = E = A = N = 4.0
        agent_type = 'B'
    else:
        persona_label = participant.get('assigned_persona') or participant.get('persona') or 'A'
        mu = config.CENTROIDS.get(persona_label, config.CENTROIDS['A'])
        E = float(mu[0])
        A = float(mu[1])
        C = float(mu[2])
        ES = float(mu[3])
        O = float(mu[4])
        N = float(8.0 - ES)
        agent_type = persona_label

    system_prompt = config.PROMPT_TEMPLATE.format(topic=topic_title, O=O, C=C, E=E, A=A, N=N, AGENT_TYPE=agent_type)
    
    model = config.BOT_MODEL
    temperature = config.BOT_TEMPERATURE
    
    # Build messages for API
    messages = [{"role": "system", "content": system_prompt}] + history
    
    # Call OpenAI
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=500
        )
        bot_response = response.choices[0].message.content
    except Exception as e:
        bot_response = f"[Error: {str(e)}]"
    
    # Save bot response
    db.save_message(participant_id, phase, "assistant", bot_response, bot_type, topic_id, model)
    
    # Check if phase should end
    message_count = db.get_message_count(participant_id, phase)
    phase_complete = message_count >= config.MESSAGES_PER_BOT
    
    return {
        "response": bot_response,
        "message_count": message_count,
        "messages_required": config.MESSAGES_PER_BOT,
        "phase_complete": phase_complete
    }


@app.post("/api/chat/stream")
async def chat_stream(request: Request):
    """Send message and stream bot response."""
    data = await request.json()
    participant_id = data.get("participant_id")
    phase = data.get("phase", 1)
    message = data.get("message", "").strip()
    
    if not participant_id or not message:
        raise HTTPException(400, "Missing participant_id or message")
    
    # Get bot type and topic from request
    bot_type = data.get("bot_type", "high_match")
    topic = data.get("topic", {})
    topic_title = topic.get("title", "general discussion")
    topic_id = topic.get("id", "unknown")
    
    # Save user message
    db.save_message(participant_id, phase, "user", message, bot_type, topic_id)
    
    # Get chat history
    history = db.get_messages(participant_id, phase)
    
    # Select prompt based on bot_type ('default' or 'persona') and assigned persona
    participant = db.get_participant(participant_id) or {}
    if bot_type == 'default':
        O = C = E = A = N = 4.0
        agent_type = 'B'
    else:
        persona_label = participant.get('assigned_persona') or participant.get('persona') or 'A'
        mu = config.CENTROIDS.get(persona_label, config.CENTROIDS['A'])
        E = float(mu[0])
        A = float(mu[1])
        C = float(mu[2])
        ES = float(mu[3])
        O = float(mu[4])
        N = float(8.0 - ES)
        agent_type = persona_label

    system_prompt = config.PROMPT_TEMPLATE.format(topic=topic_title, O=O, C=C, E=E, A=A, N=N, AGENT_TYPE=agent_type)
    
    model = config.BOT_MODEL
    temperature = config.BOT_TEMPERATURE
    
    messages = [{"role": "system", "content": system_prompt}] + history
    
    async def generate():
        full_response = ""
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=500,
                stream=True
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield f"data: {json.dumps({'content': content})}\n\n"
            
            # Save complete response
            db.save_message(participant_id, phase, "assistant", full_response, bot_type, topic_id, model)
            
            # Send completion signal
            message_count = db.get_message_count(participant_id, phase)
            yield f"data: {json.dumps({'done': True, 'message_count': message_count, 'phase_complete': message_count >= config.MESSAGES_PER_BOT})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/rating")
async def save_rating(request: Request):
    """Save bot rating."""
    data = await request.json()
    participant_id = data.get("participant_id")
    phase = data.get("phase", 1)
    bot_type = data.get("bot_type", "")
    topic_id = data.get("topic_id", "")
    rating = data.get("rating", {})
    
    if not participant_id:
        raise HTTPException(400, "Missing participant_id")
    
    db.save_rating(participant_id, phase, bot_type, topic_id, rating)
    return {"status": "ok"}


# Preference endpoint removed — study finalizes immediately after second chat.


@app.post("/api/complete")
async def complete_study(request: Request):
    """Mark study as complete."""
    data = await request.json()
    participant_id = data.get("participant_id")
    phase = data.get("phase")
    bot_type = data.get("bot_type", "")
    topic_id = data.get("topic_id", "")

    if not participant_id:
        raise HTTPException(400, "Missing participant_id")

    # If we have phase/bot/topic info, save a metrics-only rating row (no user ratings)
    try:
        if phase and bot_type:
            db.save_rating(participant_id, phase, bot_type, topic_id, {})
    except Exception:
        # do not fail completion if metrics saving fails; still mark complete
        pass

    db.mark_complete(participant_id)
    return {"status": "ok"}


@app.get("/api/export")
async def export_data():
    """Export all data as JSON (for researchers)."""
    return JSONResponse(db.export_data())


@app.get("/api/config")
async def get_config():
    """Get public config for frontend."""
    return {
        "messages_per_bot": config.MESSAGES_PER_BOT,
        "tipi_items": config.TIPI_ITEMS,
        "rating_questions": config.RATING_QUESTIONS,
        "topics": {
            "a": config.TOPIC_A,
            "b": config.TOPIC_B
        }
    }


# =============================================================================
# Admin Endpoints - Protected by secret
# =============================================================================

@app.get("/admin/data")
async def download_all_data(secret: str = Query(...)):
    """Download all CSV data as a ZIP file. Requires admin secret."""
    if secret != config.ADMIN_SECRET:
        raise HTTPException(403, "Invalid admin secret")
    
    # Create ZIP in memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename in ['participants.csv', 'messages.csv', 'ratings.csv']:
            filepath = db.DATA_DIR / filename
            if filepath.exists():
                zf.write(filepath, filename)
    
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=study_data.zip"}
    )


@app.get("/admin/data/{filename}")
async def download_single_file(filename: str, secret: str = Query(...)):
    """Download a single CSV file. Requires admin secret."""
    if secret != config.ADMIN_SECRET:
        raise HTTPException(403, "Invalid admin secret")
    
    if filename not in ['participants.csv', 'messages.csv', 'ratings.csv']:
        raise HTTPException(404, "File not found")
    
    filepath = db.DATA_DIR / filename
    if not filepath.exists():
        raise HTTPException(404, "File not found")
    
    return FileResponse(filepath, filename=filename, media_type="text/csv")


@app.get("/admin/stats")
async def get_stats(secret: str = Query(...)):
    """Get study statistics. Requires admin secret."""
    if secret != config.ADMIN_SECRET:
        raise HTTPException(403, "Invalid admin secret")
    
    import csv
    stats = {"participants": 0, "completed": 0, "messages": 0, "ratings": 0}
    
    # Count participants
    if db.PARTICIPANTS_FILE.exists():
        with open(db.PARTICIPANTS_FILE) as f:
            reader = csv.DictReader(f)
            for row in reader:
                stats["participants"] += 1
                if row.get("completed_at"):
                    stats["completed"] += 1
    
    # Count messages
    if db.MESSAGES_FILE.exists():
        with open(db.MESSAGES_FILE) as f:
            stats["messages"] = sum(1 for _ in f) - 1  # minus header
    
    # Count ratings
    if db.RATINGS_FILE.exists():
        with open(db.RATINGS_FILE) as f:
            stats["ratings"] = sum(1 for _ in f) - 1  # minus header
    
    return stats


def main():
    """Entry point for uv run."""
    import uvicorn
    print(f"\n🚀 Homophily Study Server")
    print(f"   ├── URL: http://localhost:{config.PORT}")
    print(f"   ├── API Docs: http://localhost:{config.PORT}/docs")
    print(f"   └── Press Ctrl+C to stop\n")
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")


if __name__ == "__main__":
    main()
