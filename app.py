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
import config
import database as db

app = FastAPI(title="Homophily Study", description="AI Conversation Study Platform")

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
    
    # Determine bot assignment based on group and outlier status
    # Group A: Chat1=HighMatch+TopicA, Chat2=LowMatch+TopicB
    # Group B: Chat1=LowMatch+TopicB, Chat2=HighMatch+TopicA
    # If outlier (Low E/Low A): FLIP the match labels (their "match" is the reserved bot)
    
    if group == "A":
        chat1_bot = "low_match" if is_outlier else "high_match"
        chat1_topic = config.TOPIC_A
        chat2_bot = "high_match" if is_outlier else "low_match"
        chat2_topic = config.TOPIC_B
    else:  # Group B
        chat1_bot = "high_match" if is_outlier else "low_match"
        chat1_topic = config.TOPIC_B
        chat2_bot = "low_match" if is_outlier else "high_match"
        chat2_topic = config.TOPIC_A
    
    return {
        "status": "ok",
        "assignment": {
            "group": group,
            "is_outlier": is_outlier,
            "big_five": result['big_five'],
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
    
    # Select prompt based on bot type
    if bot_type == "high_match":
        system_prompt = config.HIGH_MATCH_PROMPT.format(topic=topic_title)
    else:
        system_prompt = config.LOW_MATCH_PROMPT.format(topic=topic_title)
    
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
    
    # Select prompt based on bot type
    if bot_type == "high_match":
        system_prompt = config.HIGH_MATCH_PROMPT.format(topic=topic_title)
    else:
        system_prompt = config.LOW_MATCH_PROMPT.format(topic=topic_title)
    
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


@app.post("/api/preference")
async def save_preference(request: Request):
    """Save final bot preference (which bot user preferred)."""
    data = await request.json()
    participant_id = data.get("participant_id")
    preferred_bot = data.get("preferred_bot", "")  # "first" or "second"
    reason = data.get("reason", "")
    
    if not participant_id:
        raise HTTPException(400, "Missing participant_id")
    
    db.save_preference(participant_id, preferred_bot, reason)
    return {"status": "ok"}


@app.post("/api/complete")
async def complete_study(request: Request):
    """Mark study as complete."""
    data = await request.json()
    participant_id = data.get("participant_id")
    
    if not participant_id:
        raise HTTPException(400, "Missing participant_id")
    
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
