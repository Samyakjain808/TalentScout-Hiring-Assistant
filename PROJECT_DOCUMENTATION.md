# TalentScout Hiring Assistant — Project Documentation

---

## 1. Project Overview

**TalentScout Hiring Assistant** is an AI-powered recruitment chatbot built for TalentScout, a technology-focused staffing agency. It conducts structured candidate interviews through a conversational interface, collecting personal information and generating tailored technical questions using Google's Gemini AI.

**Live Repository:** [github.com/Samyakjain808/TalentScout-Hiring-Assistant](https://github.com/Samyakjain808/TalentScout-Hiring-Assistant)

### Key Highlights
- 🤖 AI-generated technical interview questions via Google Gemini
- 📋 Step-by-step candidate data collection with real-time validation
- 🎨 Premium dark/light mode UI with animated chat bubbles
- 🌐 Multi-language support (English, Spanish, French, Hindi, German)
- 📥 One-click JSON data export
- 💬 Basic sentiment detection for conversational awareness
- ☁️ Streamlit Cloud deployment ready

---

## 2. Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit | Web-based chat UI with sidebar controls |
| **Backend** | Python 3.9+ | Business logic, validation, state management |
| **LLM** | Google Gemini 2.5 Flash (Free Tier) | Technical question generation |
| **Storage** | Local JSON file | Candidate data persistence |
| **Env Management** | python-dotenv | Secure API key handling |
| **Data Processing** | Pandas | Data manipulation support |

---

## 3. Architecture

### 3.1 Folder Structure

```
talentscout/
├── app.py                  # Entry point — wires UI, chatbot, and session state
├── requirements.txt        # Python dependencies
├── .env.example            # API key template (safe for Git)
├── .env                    # Actual API key (git-ignored)
├── .gitignore              # Excludes .env, __pycache__, venv
├── README.md               # Setup and usage guide
├── PROJECT_DOCUMENTATION.md # This file
├── src/
│   ├── __init__.py         # Package initializer
│   ├── chatbot.py          # Core conversation engine (state machine)
│   ├── prompts.py          # All LLM prompt templates
│   ├── validators.py       # Input validation + sentiment detection
│   ├── storage.py          # JSON-based persistence layer
│   ├── ui.py               # Streamlit UI components + custom CSS
│   └── utils.py            # Helper utilities
└── data/
    └── candidates.json     # Persisted candidate records
```

### 3.2 Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `app.py` | Streamlit page config, session init, main loop, chat I/O |
| `chatbot.py` | State machine logic, Gemini API calls, interview flow orchestration |
| `prompts.py` | All prompt templates: system prompt, greeting, tech questions, farewell |
| `validators.py` | Regex validation (email, phone, name, experience), exit detection, sentiment |
| `storage.py` | Read/write candidate JSON, export formatting |
| `ui.py` | CSS injection, header, sidebar, chat history rendering |
| `utils.py` | Typing animation, progress calculator, step label formatter |

### 3.3 Data Flow Diagram

```
User Input → app.py → chatbot.handle_message()
                          │
                          ├── validators.py (validate input)
                          ├── prompts.py (get next question / build LLM prompt)
                          ├── Gemini API (generate tech questions)
                          └── storage.py (persist candidate data)
                          │
                      Response → app.py → ui.render_chat_history() → Browser
```

---

## 4. Chat Flow

The interview follows a 7-step sequential flow:

```
┌─────────────┐
│  GREETING   │ → Welcome message + ask for name
└──────┬──────┘
       ▼
┌─────────────┐
│  FULL NAME  │ → Validate: letters only, ≥2 chars
└──────┬──────┘
       ▼
┌─────────────┐
│   EMAIL     │ → Validate: RFC-5322 regex
└──────┬──────┘
       ▼
┌─────────────┐
│   PHONE     │ → Validate: 7-15 digits, optional +
└──────┬──────┘
       ▼
┌─────────────┐
│ EXPERIENCE  │ → Validate: numeric, 0-50 range
└──────┬──────┘
       ▼
┌─────────────┐
│  POSITION   │ → Free text, ≥2 chars
└──────┬──────┘
       ▼
┌─────────────┐
│  LOCATION   │ → Free text, ≥2 chars
└──────┬──────┘
       ▼
┌─────────────┐
│ TECH STACK  │ → Parse comma-separated → call Gemini API
└──────┬──────┘
       ▼
┌─────────────┐
│  QUESTIONS  │ → 3 questions × N technologies, asked one-by-one
└──────┬──────┘
       ▼
┌─────────────┐
│  SUMMARY    │ → Display table + save to JSON + farewell
└─────────────┘
```

---

## 5. Prompt Engineering

All prompts are centralized in `src/prompts.py` for easy iteration.

### 5.1 System Prompt

Sets the AI's personality: warm, professional, concise, privacy-respecting. Prevents prompt leaking and off-topic drift.

### 5.2 Tech Question Generation Prompt

```python
tech_question_prompt(["Python", "React", "PostgreSQL"], experience_years=3)
```

This dynamically builds a prompt that:
- Identifies experience level (junior/mid/senior) from years
- Lists the candidate's technologies
- Requests 3 practical, scenario-based questions per technology
- Demands structured JSON output for reliable parsing

### 5.3 Fallback Handling

When Gemini's JSON response can't be parsed (network error, malformed output), the system generates sensible default questions per technology — ensuring the interview never breaks.

### 5.4 Multi-Language Support

Language suffixes are appended to prompts (e.g., "Respond entirely in Hindi"), allowing the AI to conduct interviews in 5 languages.

---

## 6. Validation System

| Field | Validation Rule | Regex / Logic |
|-------|----------------|---------------|
| Name | ≥2 chars, letters/spaces/hyphens only | `^[a-zA-Z\s.\-']+$` |
| Email | RFC-5322 simplified format | `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$` |
| Phone | 7-15 digits, optional `+`, allows spaces/dashes | `^\+?\d{7,15}$` (after stripping) |
| Experience | Numeric, 0-50 range | `float()` conversion + range check |
| Tech Stack | At least 1 technology after parsing | Split on `,/;` and `and` |

Invalid inputs return specific error messages and re-prompt the same question.

---

## 7. Session State Management

Streamlit's `session_state` maintains the full interview context:

| Key | Type | Purpose |
|-----|------|---------|
| `chat_history` | list | All messages (role + content) |
| `current_step` | str | Active step: greeting, name, email, ..., completed |
| `step_index` | int | Index into the step order list |
| `candidate_data` | dict | Collected candidate fields |
| `tech_stack_list` | list | Parsed technologies |
| `questions` | dict | `{tech: [q1, q2, q3]}` from Gemini |
| `answers` | dict | `{tech: {question: answer}}` |
| `current_tech_idx` | int | Which technology is being asked |
| `current_q_idx` | int | Which question within that tech |
| `completed` | bool | Interview finished flag |
| `language` | str | Selected UI language |
| `dark_mode` | bool | Theme toggle state |

---

## 8. Gemini API Integration

### Configuration
```python
import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.5-flash")
```

### Key Design Decisions
- **Lazy initialization**: Model is created on first API call, not at import time
- **Singleton pattern**: Single model instance reused across all calls
- **Graceful degradation**: If API fails, fallback questions are generated locally
- **Model choice**: `gemini-2.5-flash` — fast, free-tier, high quality

---

## 9. UI Design

### 9.1 Custom CSS Features
- **Gradient header** with purple-to-pink text
- **Animated chat bubbles** with `fadeSlideIn` keyframe animation
- **Dark/Light theme** toggle with full CSS variable switching
- **Glassmorphism sidebar** with blur and translucent backgrounds
- **Custom scrollbar** with accent-colored thumb
- **Inter font** from Google Fonts for modern typography
- **Progress bar** with gradient fill and smooth transitions

### 9.2 Sidebar Components
- Current Step badge (color-coded)
- Live progress percentage with animated bar
- Collected candidate info display
- Language selector (5 languages)
- Dark mode toggle
- JSON export download button
- Reset conversation button

---

## 10. Bonus Features

| Feature | Implementation |
|---------|---------------|
| **Sentiment Detection** | Keyword-matching against positive/negative word sets in `validators.py` |
| **Progress Bar** | Calculated from `(info steps completed + questions answered) / total` |
| **Typing Animation** | Character-by-character rendering via `st.empty()` placeholder (in `utils.py`) |
| **Multi-Language** | Language suffix appended to Gemini prompts; 5 languages supported |
| **Dark Mode** | Full CSS variable swap triggered by sidebar toggle |
| **Exit Detection** | Matches against `{exit, quit, stop, bye, goodbye, end, cancel}` |
| **Data Export** | `st.download_button` with JSON serialization of candidate + answers |

---

## 11. Setup & Running

### Prerequisites
- Python 3.9+
- Free Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)

### Steps
```bash
git clone https://github.com/Samyakjain808/TalentScout-Hiring-Assistant.git
cd TalentScout-Hiring-Assistant
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env           # Add your GEMINI_API_KEY
streamlit run app.py
```

App opens at `http://localhost:8501`.

---

## 12. Deployment (Streamlit Cloud)

1. Push code to GitHub (done ✅)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect the repository
4. Set main file: `app.py`
5. Add secret: `GEMINI_API_KEY = "your_key"`
6. Deploy

---

## 13. Security & Privacy

- `.env` file is git-ignored — API keys never committed
- No sensitive data (SSN, passwords, bank info) is requested
- All data stored locally in `data/candidates.json`
- Session data isolated per browser session
- System prompt prevents prompt injection/leaking

---

## 14. Future Enhancements

- Resume/CV upload and parsing
- Answer scoring with AI evaluation
- Email notifications to recruiters
- Database backend (PostgreSQL/MongoDB)
- Admin dashboard for reviewing candidates
- Voice input support
- Integration with ATS (Applicant Tracking Systems)

---

*Built with Python, Streamlit, and Google Gemini AI*
