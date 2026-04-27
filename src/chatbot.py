"""
chatbot.py — Core conversation engine for TalentScout Hiring Assistant.

Orchestrates the multi-step interview flow:
  1. Greet → 2. Collect info → 3. Generate tech questions →
  4. Ask questions → 5. Summarise → 6. Farewell

Uses Google Gemini (free tier) for question generation and answer evaluation.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import google.generativeai as genai

from src.prompts import (
    STEP_ORDER,
    SYSTEM_PROMPT,
    evaluate_answer_prompt,
    farewell_prompt,
    get_language_suffix,
    greeting_prompt,
    next_question,
    tech_question_prompt,
)
from src.validators import (
    detect_sentiment,
    is_exit_command,
    parse_tech_stack,
    validate_email,
    validate_experience,
    validate_name,
    validate_phone,
)
from src.storage import save_candidate

# ── Gemini Configuration ───────────────────────────────────────────────
_model: Optional[genai.GenerativeModel] = None


def _get_model() -> genai.GenerativeModel:
    """Lazily initialise the Gemini model singleton."""
    global _model
    if _model is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. "
                "Please add it to your .env file or environment variables."
            )
        genai.configure(api_key=api_key)
        _model = genai.GenerativeModel("gemini-2.5-flash")
    return _model


def _call_gemini(prompt: str, language: str = "English") -> str:
    """Send a prompt to Gemini and return the text response."""
    try:
        model = _get_model()
        lang_suffix = get_language_suffix(language)
        full_prompt = prompt + lang_suffix
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        return f"⚠️ LLM Error: {str(e)}"


# ── Validators per step ────────────────────────────────────────────────
_VALIDATORS = {
    "name":       validate_name,
    "email":      validate_email,
    "phone":      validate_phone,
    "experience": validate_experience,
}


# ── Session State Initialisation ───────────────────────────────────────
def init_session(state: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all required keys exist in session state."""
    defaults = {
        "chat_history": [],
        "current_step": "greeting",
        "step_index": 0,
        "candidate_data": {},
        "tech_stack_list": [],
        "questions": {},          # {tech: [q1, q2, q3]}
        "answers": {},            # {tech: {q: answer}}
        "current_tech_idx": 0,
        "current_q_idx": 0,
        "completed": False,
        "language": "English",
        "dark_mode": True,
    }
    for key, val in defaults.items():
        if key not in state:
            state[key] = val
    return state


def reset_session(state: Dict[str, Any]) -> None:
    """Clear all conversation state for a fresh start."""
    keys_to_remove = [
        "chat_history", "current_step", "step_index", "candidate_data",
        "tech_stack_list", "questions", "answers", "current_tech_idx",
        "current_q_idx", "completed",
    ]
    for key in keys_to_remove:
        if key in state:
            del state[key]


# ── Main Response Handler ─────────────────────────────────────────────
def handle_message(user_input: str, state: Dict[str, Any]) -> str:
    """Process the user's message and return the assistant's reply.

    This is the central dispatcher that routes based on `current_step`.
    """
    # ── Exit detection ────────────────────────────────────────────
    if is_exit_command(user_input):
        name = state["candidate_data"].get("name", "Candidate")
        state["completed"] = True
        state["current_step"] = "completed"
        return farewell_prompt(name)

    # ── Sentiment logging (bonus) ─────────────────────────────────
    sentiment = detect_sentiment(user_input)
    # Could be stored or surfaced in sidebar; kept lightweight here.

    step = state["current_step"]

    # ── Greeting (first message is always the name) ───────────────
    if step == "greeting":
        state["current_step"] = STEP_ORDER[0]  # "name"
        state["step_index"] = 0
        return greeting_prompt()

    # ── Info collection steps ─────────────────────────────────────
    if step in STEP_ORDER:
        return _handle_info_step(user_input, state)

    # ── Technical questions ───────────────────────────────────────
    if step == "tech_questions":
        return _handle_tech_question(user_input, state)

    # ── Already completed ─────────────────────────────────────────
    if step == "completed":
        return "The interview has already been completed. Click **Reset** in the sidebar to start a new session."

    return "🤔 Something went wrong. Please click **Reset** and try again."


# ── Info Collection Logic ──────────────────────────────────────────────
def _handle_info_step(user_input: str, state: Dict[str, Any]) -> str:
    """Validate input for the current step and advance."""
    step = state["current_step"]
    idx = state["step_index"]

    # Validate if a validator exists for this step
    validator = _VALIDATORS.get(step)
    if validator:
        ok, result = validator(user_input)
        if not ok:
            return f"⚠️ {result}"
        state["candidate_data"][step] = result
    else:
        # Free-text steps: position, location, tech_stack
        value = user_input.strip()
        if len(value) < 2:
            return "⚠️ Please provide a more detailed answer."
        state["candidate_data"][step] = value

    # Special handling for tech_stack: parse into list
    if step == "tech_stack":
        stack = parse_tech_stack(user_input)
        if not stack:
            return "⚠️ Please list at least one technology (comma-separated)."
        state["tech_stack_list"] = stack
        state["candidate_data"]["tech_stack"] = stack

    # Advance to next step
    idx += 1
    if idx < len(STEP_ORDER):
        next_step = STEP_ORDER[idx]
        state["current_step"] = next_step
        state["step_index"] = idx
        # Build a positive acknowledgement + next question
        ack = _acknowledge(step, sentiment=detect_sentiment(user_input))
        return f"{ack}\n\n{next_question(next_step)}"
    else:
        # All info collected → generate tech questions
        return _transition_to_tech_questions(state)


def _acknowledge(step: str, sentiment: str = "neutral") -> str:
    """Return a short acknowledgement for the collected field."""
    acks = {
        "name": "Nice to meet you! 😊",
        "email": "Got it! 📧",
        "phone": "Phone number saved! 📱",
        "experience": "Thanks for sharing! 💼",
        "position": "Great choice! 🎯",
        "location": "Noted! 📍",
        "tech_stack": "Awesome tech stack! 🛠️",
    }
    base = acks.get(step, "✅ Recorded!")
    if sentiment == "positive":
        base += " Glad to hear you're enthusiastic!"
    return base


# ── Transition to Tech Questions ──────────────────────────────────────
def _transition_to_tech_questions(state: Dict[str, Any]) -> str:
    """Generate technical questions via Gemini and start the Q&A phase."""
    stack = state["tech_stack_list"]
    exp = float(state["candidate_data"].get("experience", 1))

    prompt = tech_question_prompt(stack, exp)
    raw = _call_gemini(prompt, state.get("language", "English"))

    # Parse the JSON response
    questions = _parse_questions_json(raw, stack)
    state["questions"] = questions
    state["answers"] = {tech: {} for tech in questions}
    state["current_tech_idx"] = 0
    state["current_q_idx"] = 0
    state["current_step"] = "tech_questions"

    # Deliver the first question
    first_msg = (
        "🎓 **Excellent!** I've prepared some technical questions based on your stack.\n\n"
        "Take your time — there are no wrong answers.\n\n"
    )
    first_q = _current_question_text(state)
    return first_msg + first_q


def _parse_questions_json(raw: str, fallback_stack: list) -> Dict[str, List[str]]:
    """Attempt to parse Gemini's JSON output; fall back to defaults."""
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw).strip()
    cleaned = cleaned.strip("`").strip()

    try:
        data = json.loads(cleaned)
        if "questions" in data:
            return data["questions"]
        # Maybe the model returned the dict directly
        if isinstance(data, dict) and all(isinstance(v, list) for v in data.values()):
            return data
    except (json.JSONDecodeError, TypeError):
        pass

    # Fallback: generate simple default questions
    default_qs: Dict[str, List[str]] = {}
    for tech in fallback_stack:
        default_qs[tech] = [
            f"Describe a project where you used {tech} extensively.",
            f"What are the key advantages and limitations of {tech}?",
            f"How do you handle debugging and testing in {tech}?",
        ]
    return default_qs


# ── Tech Question Handling ─────────────────────────────────────────────
def _current_question_text(state: Dict[str, Any]) -> str:
    """Format the current question with tech context and numbering."""
    techs = list(state["questions"].keys())
    t_idx = state["current_tech_idx"]
    q_idx = state["current_q_idx"]

    if t_idx >= len(techs):
        return ""

    tech = techs[t_idx]
    qs = state["questions"][tech]
    total_techs = len(techs)
    total_qs = len(qs)

    return (
        f"**🔹 {tech}** (Technology {t_idx + 1}/{total_techs}) — "
        f"Question {q_idx + 1}/{total_qs}\n\n"
        f"_{qs[q_idx]}_"
    )


def _handle_tech_question(user_input: str, state: Dict[str, Any]) -> str:
    """Record the answer and serve the next question or finish."""
    techs = list(state["questions"].keys())
    t_idx = state["current_tech_idx"]
    q_idx = state["current_q_idx"]

    if t_idx >= len(techs):
        return _finish_interview(state)

    tech = techs[t_idx]
    qs = state["questions"][tech]
    question = qs[q_idx]

    # Store the answer
    state["answers"][tech][question] = user_input.strip()

    # Advance question index
    q_idx += 1
    if q_idx >= len(qs):
        # Move to next technology
        t_idx += 1
        q_idx = 0

    state["current_tech_idx"] = t_idx
    state["current_q_idx"] = q_idx

    if t_idx >= len(techs):
        return _finish_interview(state)

    return f"✅ Answer recorded!\n\n{_current_question_text(state)}"


# ── Finish Interview ──────────────────────────────────────────────────
def _finish_interview(state: Dict[str, Any]) -> str:
    """Summarise candidate data, persist, and deliver farewell."""
    cd = state["candidate_data"]
    name = cd.get("name", "Candidate")
    total_answers = sum(len(a) for a in state["answers"].values())

    # Build summary
    summary = (
        "---\n"
        "## 📋 Interview Summary\n\n"
        f"| Field | Value |\n"
        f"|-------|-------|\n"
        f"| **Name** | {cd.get('name', 'N/A')} |\n"
        f"| **Email** | {cd.get('email', 'N/A')} |\n"
        f"| **Phone** | {cd.get('phone', 'N/A')} |\n"
        f"| **Experience** | {cd.get('experience', 'N/A')} years |\n"
        f"| **Position** | {cd.get('position', 'N/A')} |\n"
        f"| **Location** | {cd.get('location', 'N/A')} |\n"
        f"| **Tech Stack** | {', '.join(cd.get('tech_stack', []))} |\n"
        f"| **Questions Answered** | {total_answers} |\n\n"
        "---\n\n"
    )

    # Persist
    record = {
        "candidate": cd,
        "answers": state["answers"],
        "questions": state["questions"],
    }
    save_candidate(record)

    state["completed"] = True
    state["current_step"] = "completed"

    return summary + farewell_prompt(name)


# ── Total Questions Count (for progress) ──────────────────────────────
def total_question_count(state: Dict[str, Any]) -> int:
    """Return total number of technical questions across all techs."""
    return sum(len(qs) for qs in state.get("questions", {}).values())


def answered_count(state: Dict[str, Any]) -> int:
    """Return number of questions answered so far."""
    return sum(len(a) for a in state.get("answers", {}).values())
