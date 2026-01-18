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

# Bot models - use any OpenAI model
BOT_1_MODEL = "gpt-4o"          # First conversation
BOT_2_MODEL = "gpt-4o-mini"     # Second conversation (or same model, different persona)

# Temperature settings (0.0 = deterministic, 1.0 = creative)
BOT_1_TEMPERATURE = 0.7
BOT_2_TEMPERATURE = 0.7

# =============================================================================
# Bot Personas
# =============================================================================

BOT_1_SYSTEM_PROMPT = """You are a friendly, casual conversational AI assistant.

Your personality traits:
- Warm and approachable
- Uses casual language and occasional humor
- Shows genuine interest in the user
- Asks follow-up questions
- Shares relevant personal anecdotes (as an AI)

Keep responses concise (2-3 sentences typically). Be engaging but not overwhelming.
"""

BOT_2_SYSTEM_PROMPT = """You are a professional, knowledgeable AI assistant.

Your personality traits:
- Polite and formal
- Precise and informative
- Structured responses
- Focus on accuracy
- Maintains professional distance

Keep responses concise (2-3 sentences typically). Be helpful but professional.
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
