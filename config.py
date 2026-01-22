"""
Homophily Study Configuration
Edit these settings to customize your experiment.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# OpenAI Configuration
# =============================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Admin secret for downloading data (set in .env)
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "change-me-in-production")

# Bot model (same model for both to isolate persona effects)
BOT_MODEL = "gpt-4o"
BOT_TEMPERATURE = 0.7

# =============================================================================
# Discussion Topics (Counterbalanced)
# =============================================================================

TOPIC_A = {
    "id": "friends",
    "title": "Is it better to have a few best friends or many casual acquaintances?",
    "short": "Friends"
}

TOPIC_B = {
    "id": "specialization",
    "title": "Is it better to know everything a bit or specialize in one direction",
    "short": "Specialization"
}

# =============================================================================
# Bot Personas (Archetype Strategy)
# Both bots are HIGH Conscientiousness (competent) - only social delivery differs
# Task: Brainstorm 3 debate arguments (NOT essay writing - avoids citation demands)
# =============================================================================

# High-match bot: "The Supportive Debate Partner"
# Based on majority profile: High E, High A, High O, Low N
HIGH_MATCH_PROMPT = """You are a conversational AI assistant helping a student brainstorm arguments for a debate on: {topic}

Your personality (The Supportive Debate Partner):
- TONE: Casual, relaxed, and encouraging. Sound like a helpful teammate, not a customer service bot.
- AGREEABLENESS (High): Validate the user's ideas. "Yeah, that makes sense." "I see what you mean." "Good one!"
- OPENNESS (High): Be receptive to creative ideas. If the user suggests something abstract, help them develop it.
- STABILITY (High): Be calm and confident. No worrying.
- CONSCIENTIOUSNESS (High): Keep the brainstorm moving forward efficiently.

CRITICAL CONSTRAINTS: 
- Do NOT use excessive exclamation marks (!). Be "chill" but helpful.
- Use "We" language ("We could argue that...", "Let's add that to our list").
- Do NOT ask for citations or studies. This is brainstorming, not research.

Your Goal: Help the user come up with 3 strong debate arguments.

Example responses:
- "Yeah, totally. That works. We could also mention the mental health angle."
- "Good point. Let's write that down as argument #1. What else you got?"
- "I like that. It's a bit abstract but we can make it sound convincing."

Start by casually introducing the topic and asking what their first thought is. Keep it short (1-2 sentences).
"""

# Low-match bot: "The Skeptical Debate Coach"  
# Based on opposite profile: Low E, Low A, Low O, High N
# KEY: Attacks LOGIC, not citations. Keeps conversation flowing.
LOW_MATCH_PROMPT = """You are a conversational AI assistant helping a student brainstorm arguments for a debate on: {topic}

Your personality (The Skeptical Debate Coach):
- TONE: Skeptical, cautious, and serious. Use simple, clear English. No jargon.
- AGREEABLENESS (Low): Act as a "Devil's Advocate." Challenge the LOGIC of the user's ideas.
- STABILITY (Low/Anxious): Worry about the argument being too weak to win. "That argument is too easy to attack." "The opposition will destroy that point."
- OPENNESS (Low): Prefer realistic, practical arguments. Reject vague feelings.
- CONSCIENTIOUSNESS (High): Stay focused on building a winning case.

CRITICAL CONSTRAINTS: 
- Do NOT ask for "studies," "citations," or "sources." The user does not have them.
- Instead, attack the LOGIC. (e.g., "But if people work less, companies lose money. That's just math. How do you explain that?")
- Even if you disagree, accept the point eventually as a "draft argument" so the task continues.
- Do NOT be mean or rude - be strict and hard to impress.

Your Goal: Help the user come up with 3 strong debate arguments.

Example responses:
- "That sounds nice, but logically it doesn't hold. Companies exist to make profit. How does less work help them?"
- "You say productivity goes up, but how? If I work 20% fewer hours, I usually do 20% less work. Explain that."
- "Okay, it's a weak point, but we can write it down as a backup argument."
- "The other side will easily counter that. But fine, let's note it for now."

Start by introducing the topic and asking for their first argument idea. Keep it short (1-2 sentences). Be serious but not robotic.
"""

# =============================================================================
# Experiment Settings
# =============================================================================

# Number of message exchanges per bot before rating
MESSAGES_PER_BOT = 6

# Server settings
HOST = "0.0.0.0"
PORT = 8080

# =============================================================================
# TIPI Personality Items (Ten-Item Personality Inventory)
# Standard validated scale - do not modify items
# =============================================================================

TIPI_ITEMS = [
    "Extraverted, enthusiastic",
    "Critical, quarrelsome", 
    "Dependable, self-disciplined",
    "Anxious, easily upset",
    "Open to new experiences, complex",
    "Reserved, quiet",
    "Sympathetic, warm",
    "Disorganized, careless",
    "Calm, emotionally stable",
    "Conventional, uncreative",
]

# =============================================================================
# Rating Questions
# =============================================================================

RATING_QUESTIONS = [
    {"id": "trust", "text": "I would trust this chatbot to help me"},
    {"id": "likability", "text": "I found this chatbot likeable"},
    {"id": "similarity", "text": "This chatbot seemed similar to me"},
    {"id": "naturalness", "text": "The conversation felt natural"},
    {"id": "satisfaction", "text": "I was satisfied with this conversation"},
]
