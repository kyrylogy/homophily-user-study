# Homophily Study

A modern, fast web application for conducting homophily research with AI chatbots. Built with FastAPI and streaming support.

## ✨ Features

- **🚀 Easy to Run** - Single command with uv
- **💬 Real-time Streaming** - Bot responses stream word-by-word
- **🎨 Modern Design** - Light blue theme with smooth animations
- **📊 CSV Data Collection** - Easy to analyze in Excel/Python/R
- **🤖 2 Configurable Bots** - Different personas for comparison
- **📝 Easy Feedback Forms** - Likert scales + open responses

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- OpenAI API key

### Setup & Run

```bash
# 1. Install uv (if not installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Clone and enter project
cd HomophilyStudy

# 3. Create .env file with your API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Run the application
uv run app.py
```

The app will be available at **http://localhost:8080**

### Alternative: Development Mode (with auto-reload)

```bash
uv run uvicorn app:app --reload --host 0.0.0.0 --port 8080
```

## 📁 Project Structure

```
HomophilyStudy/
├── app.py              # FastAPI server with streaming
├── config.py           # Bot settings, prompts, questions
├── database.py         # CSV data storage
├── pyproject.toml      # uv/pip dependencies
├── .env                # Your API keys (create from .env.example)
├── static/
│   ├── app.js          # Frontend with streaming support
│   └── style.css       # Modern light blue theme
├── templates/
│   └── index.html      # Single-page app
└── data/               # Auto-created CSV files
    ├── participants.csv
    ├── messages.csv
    └── ratings.csv
```

## ⚙️ Configuration

Edit `config.py` to customize:

### Bot Settings
```python
# Models
BOT_1_MODEL = "gpt-4o"          # First chatbot
BOT_2_MODEL = "gpt-4o-mini"     # Second chatbot

# Temperatures (0.0 = deterministic, 1.0 = creative)
BOT_1_TEMPERATURE = 0.7
BOT_2_TEMPERATURE = 0.7
```

### Bot Personas
```python
BOT_1_SYSTEM_PROMPT = """You are a friendly, casual conversational AI..."""
BOT_2_SYSTEM_PROMPT = """You are a professional, knowledgeable AI..."""
```

### Experiment Settings
```python
MESSAGES_PER_BOT = 6    # Messages before rating appears
PORT = 8080             # Server port
```

## 📊 Data Collection

All data is stored in simple CSV files in the `data/` folder:

### participants.csv
Demographics, personality scores (TIPI), interests, timestamps

### messages.csv  
All chat messages with participant ID, phase, role, content, model, timestamp

### ratings.csv
Likert scale ratings for trust, likability, similarity, naturalness, satisfaction + open responses

### Export as JSON
```bash
curl http://localhost:8080/api/export > study_data.json
```

## 🔬 Study Pipeline

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Welcome   │──▶│   Profile   │──▶│   Chat #1   │──▶│  Rating #1  │
│   Screen    │   │    Form     │   │   (Bot 1)   │   │   (Likert)  │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
                                                              │
┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  Thank You  │◀──│  Rating #2  │◀──│   Chat #2   │◀──────────┘
│   Screen    │   │   (Likert)  │   │   (Bot 2)   │
└─────────────┘   └─────────────┘   └─────────────┘
```

## 🛠️ API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main application |
| `/api/start` | POST | Start new session |
| `/api/profile` | POST | Save profile data |
| `/api/chat/stream` | POST | Send message (streaming) |
| `/api/rating` | POST | Save ratings |
| `/api/complete` | POST | Mark complete |
| `/api/config` | GET | Get public config |
| `/api/export` | GET | Export all data as JSON |
| `/docs` | GET | API documentation |

## 🎨 Customization

### Colors
Edit CSS variables in `static/style.css`:
```css
:root {
    --primary-500: #0ea5e9;  /* Main blue */
    --accent-gradient: linear-gradient(135deg, #0ea5e9, #06b6d4, #14b8a6);
}
```

### Rating Questions
Edit in `config.py`:
```python
RATING_QUESTIONS = [
    {"id": "trust", "text": "I would trust this chatbot to help me"},
    {"id": "likability", "text": "I found this chatbot likeable"},
    # Add more...
]
```

## 📋 Data Collection Details

### Profile Questionnaire
| Field | Type | Required |
|-------|------|----------|
| Age | Dropdown (18-24, 25-34, etc.) | ✓ |
| Gender | Dropdown | ✓ |
| Education | Dropdown | ✓ |
| TIPI-1 to TIPI-10 | 7-point Likert | ✓ |
| Interests | Text | ✓ |
| Communication Style | Dropdown | ✓ |

### Chat Sessions
- All messages logged with timestamps
- Message count tracked per phase
- Bot responses stored with model info

### Bot Ratings
| Metric | Scale |
|--------|-------|
| Trust | 1-7 Likert |
| Likability | 1-7 Likert |
| Similarity | 1-7 Likert |
| Naturalness | 1-7 Likert |
| Satisfaction | 1-7 Likert |
| Open Response | Free text |

## 🔧 Tech Stack

- **Backend**: FastAPI + Python 3.10+
- **Frontend**: Vanilla JS + CSS (no frameworks)
- **AI**: OpenAI API with streaming
- **Storage**: CSV files (easy analysis)
- **Package Manager**: uv (fast & modern)

## 📄 License

MIT License - Feel free to use for research!
