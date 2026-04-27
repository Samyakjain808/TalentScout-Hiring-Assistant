"""
app.py — Entry point for TalentScout Hiring Assistant.

Run with:
    streamlit run app.py

This module wires together the chatbot engine, UI components,
and Streamlit session state to deliver the full interview experience.
"""

import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ── Page Configuration (must be first Streamlit call) ──────────────────
st.set_page_config(
    page_title="TalentScout Hiring Assistant",
    page_icon="🚀",
    layout="centered",
    initial_sidebar_state="expanded",
)

from src.chatbot import handle_message, init_session, reset_session
from src.ui import inject_css, render_chat_history, render_header, render_sidebar


def main() -> None:
    """Main application loop."""

    # ── Initialise session state ──────────────────────────────────
    init_session(st.session_state)

    # ── Inject custom CSS (respects dark-mode toggle) ─────────────
    inject_css(dark_mode=st.session_state.get("dark_mode", True))

    # ── Sidebar ───────────────────────────────────────────────────
    should_reset = render_sidebar(st.session_state)
    if should_reset:
        reset_session(st.session_state)
        st.rerun()

    # ── Header ────────────────────────────────────────────────────
    render_header()

    # ── Auto-greet on first visit ─────────────────────────────────
    if not st.session_state["chat_history"]:
        greeting = handle_message("", st.session_state)
        st.session_state["chat_history"].append(
            {"role": "assistant", "content": greeting}
        )

    # ── Render chat history ───────────────────────────────────────
    render_chat_history(st.session_state["chat_history"])

    # ── Chat input ────────────────────────────────────────────────
    if not st.session_state.get("completed", False):
        user_input = st.chat_input("Type your response here…")
        if user_input:
            # Display user message
            st.session_state["chat_history"].append(
                {"role": "user", "content": user_input}
            )
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_input)

            # Get bot response
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Thinking…"):
                    response = handle_message(user_input, st.session_state)
                st.markdown(response, unsafe_allow_html=True)

            st.session_state["chat_history"].append(
                {"role": "assistant", "content": response}
            )
            st.rerun()
    else:
        st.info("✅ Interview complete! Use the sidebar to **export** your data or **reset** for a new session.")


# ── Entry Point ────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
