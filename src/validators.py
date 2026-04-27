"""
validators.py — Input validation helpers for candidate data.

Provides regex-based validators for email, phone, experience,
and a sentiment detector for conversational tone analysis.
"""

import re
from typing import Tuple


# ── Email ──────────────────────────────────────────────────────────────
def validate_email(email: str) -> Tuple[bool, str]:
    """Validate email format using RFC-5322 simplified regex."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if re.match(pattern, email.strip()):
        return True, email.strip()
    return False, "Please enter a valid email address (e.g. jane@example.com)."


# ── Phone ──────────────────────────────────────────────────────────────
def validate_phone(phone: str) -> Tuple[bool, str]:
    """Accept 7-15 digit phone numbers with optional +, dashes, spaces, parens."""
    cleaned = re.sub(r"[\s\-\(\)]", "", phone.strip())
    pattern = r"^\+?\d{7,15}$"
    if re.match(pattern, cleaned):
        return True, cleaned
    return False, "Please enter a valid phone number (7–15 digits, e.g. +1234567890)."


# ── Experience ─────────────────────────────────────────────────────────
def validate_experience(exp: str) -> Tuple[bool, str]:
    """Validate years of experience is a number between 0 and 50."""
    try:
        years = float(exp.strip())
        if 0 <= years <= 50:
            return True, str(years)
        return False, "Experience must be between 0 and 50 years."
    except ValueError:
        return False, "Please enter a numeric value for years of experience."


# ── Name ───────────────────────────────────────────────────────────────
def validate_name(name: str) -> Tuple[bool, str]:
    """Ensure the name has at least 2 alphabetic characters."""
    cleaned = name.strip()
    if len(cleaned) >= 2 and re.match(r"^[a-zA-Z\s\.\-']+$", cleaned):
        return True, cleaned
    return False, "Please enter a valid name (at least 2 characters, letters only)."


# ── Tech Stack Parser ─────────────────────────────────────────────────
def parse_tech_stack(raw: str) -> list:
    """Split comma / slash / 'and' separated tech list into clean tokens."""
    techs = re.split(r"[,/;]+|\band\b", raw, flags=re.IGNORECASE)
    return [t.strip() for t in techs if t.strip()]


# ── Exit-Word Detector ────────────────────────────────────────────────
EXIT_WORDS = {"exit", "quit", "stop", "bye", "goodbye", "end", "cancel"}

def is_exit_command(text: str) -> bool:
    """Return True if the message is an exit keyword."""
    return text.strip().lower() in EXIT_WORDS


# ── Basic Sentiment Detector ──────────────────────────────────────────
POSITIVE_WORDS = {
    "great", "awesome", "thanks", "thank", "good", "love", "amazing",
    "excellent", "fantastic", "wonderful", "happy", "excited", "sure",
    "yes", "yeah", "absolutely", "perfect", "nice",
}
NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "hate", "worst", "annoyed", "frustrated",
    "angry", "disappointed", "boring", "useless", "no", "nah", "nope",
}

def detect_sentiment(text: str) -> str:
    """Return 'positive', 'negative', or 'neutral' based on keyword overlap."""
    words = set(text.lower().split())
    pos = len(words & POSITIVE_WORDS)
    neg = len(words & NEGATIVE_WORDS)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"
