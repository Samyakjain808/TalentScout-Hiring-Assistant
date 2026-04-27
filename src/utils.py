"""
utils.py — Miscellaneous utility helpers.

Provides small, reusable functions used across the application.
"""

import time
import streamlit as st


def typing_effect(text: str, speed: float = 0.02) -> None:
    """Display text character-by-character with a typing animation.

    Uses a Streamlit empty placeholder to simulate a typewriter effect.
    """
    placeholder = st.empty()
    displayed = ""
    for char in text:
        displayed += char
        placeholder.markdown(displayed)
        time.sleep(speed)


def progress_percentage(current_step_index: int, total_steps: int) -> int:
    """Return completion percentage (0–100)."""
    if total_steps <= 0:
        return 0
    return min(int((current_step_index / total_steps) * 100), 100)


def format_step_label(step: str) -> str:
    """Convert an internal step key to a human-readable label."""
    labels = {
        "name": "📛 Full Name",
        "email": "📧 Email Address",
        "phone": "📱 Phone Number",
        "experience": "💼 Years of Experience",
        "position": "🎯 Desired Position",
        "location": "📍 Current Location",
        "tech_stack": "🛠️ Tech Stack",
        "tech_questions": "❓ Technical Questions",
        "completed": "✅ Completed",
    }
    return labels.get(step, step.replace("_", " ").title())
