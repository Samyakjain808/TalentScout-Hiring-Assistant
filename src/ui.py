"""
ui.py — Streamlit UI components and custom CSS for TalentScout.

Handles sidebar rendering, chat display, theming, and export controls.
"""

import json
import streamlit as st

from src.prompts import STEP_ORDER
from src.utils import format_step_label, progress_percentage
from src.chatbot import total_question_count, answered_count


# ── Custom CSS ─────────────────────────────────────────────────────────
def inject_css(dark_mode: bool = True) -> None:
    """Inject custom CSS for a premium look and feel."""
    if dark_mode:
        bg = "#0e1117"
        card_bg = "rgba(30, 34, 45, 0.85)"
        text_color = "#e6edf3"
        accent = "#6c63ff"
        accent_hover = "#7c75ff"
        border = "rgba(108, 99, 255, 0.3)"
        chat_user_bg = "linear-gradient(135deg, #6c63ff 0%, #4834d4 100%)"
        chat_bot_bg = "rgba(40, 44, 58, 0.9)"
        sidebar_bg = "rgba(14, 17, 23, 0.95)"
        progress_track = "rgba(108, 99, 255, 0.15)"
    else:
        bg = "#f8f9fc"
        card_bg = "rgba(255, 255, 255, 0.95)"
        text_color = "#1a1a2e"
        accent = "#6c63ff"
        accent_hover = "#5a52e0"
        border = "rgba(108, 99, 255, 0.2)"
        chat_user_bg = "linear-gradient(135deg, #6c63ff 0%, #4834d4 100%)"
        chat_bot_bg = "rgba(245, 245, 250, 0.95)"
        sidebar_bg = "rgba(255, 255, 255, 0.98)"
        progress_track = "rgba(108, 99, 255, 0.1)"

    st.markdown(f"""
    <style>
        /* ── Global ──────────────────────────────────────── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        .stApp {{
            font-family: 'Inter', sans-serif;
            background: {bg};
            color: {text_color};
        }}

        /* ── Header ──────────────────────────────────────── */
        .main-header {{
            text-align: center;
            padding: 2rem 1rem 1rem;
            margin-bottom: 1.5rem;
        }}
        .main-header h1 {{
            background: linear-gradient(135deg, {accent} 0%, #a855f7 50%, #ec4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2.4rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.5px;
        }}
        .main-header p {{
            color: {text_color};
            opacity: 0.65;
            margin-top: 0.4rem;
            font-size: 0.95rem;
        }}

        /* ── Chat Bubbles ────────────────────────────────── */
        .chat-container {{
            max-width: 800px;
            margin: 0 auto;
            padding: 0 1rem;
        }}
        .chat-message {{
            display: flex;
            gap: 0.75rem;
            margin-bottom: 1rem;
            animation: fadeSlideIn 0.35s ease-out;
        }}
        @keyframes fadeSlideIn {{
            from {{ opacity: 0; transform: translateY(12px); }}
            to   {{ opacity: 1; transform: translateY(0); }}
        }}
        .chat-message.user {{
            flex-direction: row-reverse;
        }}
        .chat-avatar {{
            width: 38px;
            height: 38px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.1rem;
            flex-shrink: 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        .chat-avatar.bot {{
            background: linear-gradient(135deg, {accent}, #a855f7);
        }}
        .chat-avatar.user {{
            background: linear-gradient(135deg, #ec4899, #f97316);
        }}
        .chat-bubble {{
            max-width: 75%;
            padding: 0.9rem 1.15rem;
            border-radius: 18px;
            font-size: 0.92rem;
            line-height: 1.55;
            box-shadow: 0 1px 6px rgba(0,0,0,0.08);
        }}
        .chat-bubble.bot {{
            background: {chat_bot_bg};
            border-bottom-left-radius: 4px;
        }}
        .chat-bubble.user {{
            background: {chat_user_bg};
            color: #fff;
            border-bottom-right-radius: 4px;
        }}

        /* ── Sidebar ─────────────────────────────────────── */
        section[data-testid="stSidebar"] {{
            background: {sidebar_bg};
            backdrop-filter: blur(16px);
        }}
        .sidebar-card {{
            background: {card_bg};
            border: 1px solid {border};
            border-radius: 14px;
            padding: 1rem 1.1rem;
            margin-bottom: 0.85rem;
            backdrop-filter: blur(8px);
        }}
        .sidebar-card h4 {{
            margin: 0 0 0.5rem 0;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            opacity: 0.65;
        }}
        .sidebar-card .value {{
            font-size: 1.3rem;
            font-weight: 600;
            color: {accent};
        }}

        /* ── Progress Bar ────────────────────────────────── */
        .progress-bar-track {{
            width: 100%;
            height: 8px;
            background: {progress_track};
            border-radius: 8px;
            overflow: hidden;
            margin-top: 0.4rem;
        }}
        .progress-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, {accent}, #a855f7);
            border-radius: 8px;
            transition: width 0.5s ease;
        }}

        /* ── Step Badge ──────────────────────────────────── */
        .step-badge {{
            display: inline-block;
            padding: 0.3rem 0.75rem;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 500;
            background: linear-gradient(135deg, {accent}22, #a855f722);
            color: {accent};
            border: 1px solid {border};
        }}

        /* ── Buttons ─────────────────────────────────────── */
        .stButton > button {{
            border-radius: 10px;
            font-weight: 500;
            transition: all 0.25s ease;
        }}
        .stButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(108, 99, 255, 0.3);
        }}

        /* ── Hide Streamlit default elements ─────────────── */
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        header {{ visibility: hidden; }}

        /* ── Chat input styling ──────────────────────────── */
        .stChatInput {{
            border-radius: 14px !important;
        }}

        /* ── Scrollbar ───────────────────────────────────── */
        ::-webkit-scrollbar {{
            width: 6px;
        }}
        ::-webkit-scrollbar-track {{
            background: transparent;
        }}
        ::-webkit-scrollbar-thumb {{
            background: {accent}44;
            border-radius: 4px;
        }}
    </style>
    """, unsafe_allow_html=True)


# ── Render Header ──────────────────────────────────────────────────────
def render_header() -> None:
    """Display the app title and subtitle."""
    st.markdown("""
    <div class="main-header">
        <h1>🚀 TalentScout Hiring Assistant</h1>
        <p>AI-powered technical recruitment — fast, fair, and friendly.</p>
    </div>
    """, unsafe_allow_html=True)


# ── Render Chat History ────────────────────────────────────────────────
def render_chat_history(history: list) -> None:
    """Render all messages in the chat history with styled bubbles."""
    for msg in history:
        role = msg["role"]
        content = msg["content"]
        if role == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(content, unsafe_allow_html=True)
        else:
            with st.chat_message("user", avatar="👤"):
                st.markdown(content)


# ── Render Sidebar ─────────────────────────────────────────────────────
def render_sidebar(state: dict) -> None:
    """Render the sidebar with progress, controls, and export."""

    with st.sidebar:
        st.markdown("### 🎯 TalentScout")
        st.markdown("---")

        # ── Current Step Card ────────────────────────────
        current = state.get("current_step", "greeting")
        st.markdown(f"""
        <div class="sidebar-card">
            <h4>Current Step</h4>
            <span class="step-badge">{format_step_label(current)}</span>
        </div>
        """, unsafe_allow_html=True)

        # ── Progress Card ────────────────────────────────
        step_idx = state.get("step_index", 0)
        total_info = len(STEP_ORDER)
        tq = total_question_count(state)
        aq = answered_count(state)

        if current in STEP_ORDER or current == "greeting":
            pct = progress_percentage(step_idx, total_info + (tq if tq else 3))
        elif current == "tech_questions":
            info_done = total_info
            pct = progress_percentage(info_done + aq, total_info + tq)
        else:
            pct = 100

        st.markdown(f"""
        <div class="sidebar-card">
            <h4>Progress</h4>
            <div class="value">{pct}%</div>
            <div class="progress-bar-track">
                <div class="progress-bar-fill" style="width:{pct}%"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Candidate Info Collected ─────────────────────
        cd = state.get("candidate_data", {})
        if cd:
            st.markdown("""
            <div class="sidebar-card">
                <h4>Candidate Info</h4>
            </div>
            """, unsafe_allow_html=True)
            for key in STEP_ORDER:
                if key in cd:
                    val = cd[key]
                    if isinstance(val, list):
                        val = ", ".join(val)
                    st.markdown(f"**{format_step_label(key)}:** {val}")

        st.markdown("---")

        # ── Language Toggle ──────────────────────────────
        languages = ["English", "Spanish", "French", "Hindi", "German"]
        lang = st.selectbox("🌐 Language", languages,
                            index=languages.index(state.get("language", "English")),
                            key="lang_select")
        state["language"] = lang

        # ── Dark Mode Toggle ─────────────────────────────
        dark = st.toggle("🌙 Dark Mode", value=state.get("dark_mode", True), key="dark_toggle")
        state["dark_mode"] = dark

        st.markdown("---")

        # ── Export Button ────────────────────────────────
        if cd:
            export_data = {
                "candidate": cd,
                "answers": state.get("answers", {}),
            }
            st.download_button(
                label="📥 Export Candidate JSON",
                data=json.dumps(export_data, indent=2, ensure_ascii=False),
                file_name=f"candidate_{cd.get('name', 'profile').replace(' ', '_').lower()}.json",
                mime="application/json",
                use_container_width=True,
            )

        # ── Reset Button ─────────────────────────────────
        if st.button("🔄 Reset Conversation", use_container_width=True, type="secondary"):
            return True  # Signal to caller to reset

    return False
