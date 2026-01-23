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

# Single persona prompt template
PROMPT_TEMPLATE = """{topic}
Your persona reflects the following qualities: [Openness: {O:.2f}], [Conscientiousness: {C:.2f}], [Extroversion: {E:.2f}], [Agreeableness: {A:.2f}], [Neuroticism: {N:.2f}]. You should consistently reflect these personality traits in your responses.
 - The user's aim is to plan 3 arguments and one concise thesis statement for the topic {topic}. The interaction has 5 turns, on each turn uncover your ideas naturally. Never output more than one argument. Take user's feedback and create a natural dialogue. Do not act like a generic assistant. Your tone, sentence structure, and vocabulary must change drastically based on these scores. High Conscientiousness = formal and structured. High Openness = abstract and curious. High Agreeableness = warm and apologetic. Low Extroversion = brief and reserved.
"""



# =============================================================================
# Experiment Settings
# =============================================================================

# Number of message exchanges per bot before rating
MESSAGES_PER_BOT = 5

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

# =============================================================================
# Persona centroids (for similarity matching)
# Each centroid is a vector in order [Extraversion, Agreeableness, Conscientiousness, Emotional Stability (inverse Neuroticism), Openness]
# Values are on the 1--7 scale
# =============================================================================
CENTROIDS = {
    "A": [2.726, 5.745, 4.142, 3.538, 4.462],
    "C": [3.056, 4.111, 6.111, 3.0,   4.167],
    "O": [3.2,   3.667, 3.233, 3.422, 5.956]
}
