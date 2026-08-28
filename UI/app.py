from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from google import genai


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.chatbot import answer_question  # noqa: E402
from src.config import get_gemini_api_key  # noqa: E402


st.set_page_config(
    page_title="FAQ Assistant",
    page_icon="💬",
    layout="wide",
)


st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

        :root {
            --bg-base:     #0d0f14;
            --bg-surface:  #13161d;
            --bg-raised:   #1a1e28;
            --bg-hover:    #1f2435;
            --border:      rgba(255,255,255,0.06);
            --border-mid:  rgba(255,255,255,0.10);
            --border-hi:   rgba(255,255,255,0.16);
            --text-hi:     #f0f2f8;
            --text-mid:    #8b90a0;
            --text-lo:     #4d5268;
            --accent:      #6c8aff;
            --accent-glow: rgba(108,138,255,0.18);
            --accent-dim:  rgba(108,138,255,0.08);
            --teal:        #3ecfb2;
            --teal-dim:    rgba(62,207,178,0.10);
            --radius-sm:   8px;
            --radius-md:   14px;
            --radius-lg:   20px;
        }

        html, body, [class*="css"] {
            font-family: 'Inter', system-ui, sans-serif;
        }

        /* ── page background ── */
        .stApp {
            background: var(--bg-base);
            color: var(--text-hi);
        }
        .stApp > header { background: transparent !important; }

        /* ── hide default streamlit chrome ── */
        #MainMenu, footer, .stDeployButton { display: none !important; }
        .block-container {
            padding: 1.5rem 2rem 3rem !important;
            max-width: 1100px;
        }

        /* ══════════════════════════════════════
           SIDEBAR
        ══════════════════════════════════════ */
        [data-testid="stSidebar"] {
            background: var(--bg-surface) !important;
            border-right: 1px solid var(--border) !important;
        }
        [data-testid="stSidebar"] > div:first-child {
            padding: 1.5rem 1.2rem;
        }

        .brand-lockup {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 1.8rem;
            padding-bottom: 1.4rem;
            border-bottom: 1px solid var(--border);
        }
        .brand-icon {
            width: 34px; height: 34px;
            background: linear-gradient(135deg, var(--accent), var(--teal));
            border-radius: 9px;
            display: flex; align-items: center; justify-content: center;
            font-size: 16px;
        }
        .brand-name {
            font-size: 0.95rem;
            font-weight: 600;
            color: var(--text-hi);
            letter-spacing: -0.01em;
        }
        .brand-sub {
            font-size: 0.74rem;
            color: var(--text-mid);
            margin-top: 1px;
        }

        .sidebar-section-title {
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            color: var(--text-lo);
            margin: 1.4rem 0 0.6rem;
        }

        /* quick-prompt buttons */
        .stButton > button {
            background: var(--bg-raised) !important;
            color: var(--text-mid) !important;
            border: 1px solid var(--border-mid) !important;
            border-radius: var(--radius-sm) !important;
            font-size: 0.82rem !important;
            font-weight: 400 !important;
            padding: 0.5rem 0.75rem !important;
            text-align: left !important;
            width: 100% !important;
            transition: all 0.15s ease !important;
            line-height: 1.4 !important;
        }
        .stButton > button:hover {
            background: var(--bg-hover) !important;
            color: var(--text-hi) !important;
            border-color: var(--border-hi) !important;
        }
        /* clear-chat button accent */
        .stButton > button[kind="secondary"]:last-of-type,
        div[data-testid="stButton"]:last-of-type > button {
            color: var(--text-lo) !important;
            border-color: var(--border) !important;
            margin-top: 0.4rem;
        }

        /* audio input */
        [data-testid="stAudioInput"] {
            background: var(--bg-raised) !important;
            border: 1px solid var(--border-mid) !important;
            border-radius: var(--radius-md) !important;
        }

        /* ══════════════════════════════════════
           HEADER / HERO
        ══════════════════════════════════════ */
        .hero-wrap {
            display: flex;
            align-items: flex-start;
            justify-content: center;
            gap: 1.5rem;
            margin-bottom: 1.8rem;
            padding-bottom: 1.6rem;
            border-bottom: 1px solid var(--border);
        }
        .hero-text {}
        .hero-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: var(--accent-dim);
            border: 1px solid rgba(108,138,255,0.2);
            border-radius: 999px;
            padding: 3px 12px;
            font-size: 0.72rem;
            font-weight: 500;
            color: var(--accent);
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 0.7rem;
        }
        .hero-dot {
            width: 6px; height: 6px;
            border-radius: 50%;
            background: var(--accent);
            animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50%       { opacity: 0.35; }
        }
        .hero-title {
            font-size: 1.9rem;
            font-weight: 600;
            letter-spacing: -0.03em;
            color: var(--text-hi);
            line-height: 1.1;
            margin: 0 0 0.4rem;
        }
        .hero-title span {
            background: linear-gradient(90deg, var(--accent), var(--teal));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .hero-desc {
            font-size: 0.88rem;
            color: var(--text-mid);
            max-width: 48ch;
            line-height: 1.6;
            margin: 0;
        }
        .hero-stats {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            flex-shrink: 0;
        }
        .stat-pill {
            background: var(--bg-raised);
            border: 1px solid var(--border-mid);
            border-radius: var(--radius-sm);
            padding: 0.45rem 0.9rem;
            font-size: 0.8rem;
            color: var(--text-mid);
            white-space: nowrap;
        }
        .stat-pill strong {
            color: var(--text-hi);
            font-weight: 500;
        }

        /* ══════════════════════════════════════
           CHAT MESSAGES
        ══════════════════════════════════════ */
        [data-testid="stChatMessage"] {
            background: transparent !important;
            border: none !important;
            padding: 0.6rem 0 !important;
        }

        /* user bubble */
        [data-testid="stChatMessage"][data-testid*="user"],
        .stChatMessage:has([data-testid="chatAvatarIcon-user"]) {
            flex-direction: row-reverse;
        }

        .stChatMessageContent {
            background: var(--bg-raised) !important;
            border: 1px solid var(--border-mid) !important;
            border-radius: var(--radius-md) !important;
            padding: 0.8rem 1rem !important;
            font-size: 0.9rem !important;
            line-height: 1.65 !important;
            color: var(--text-hi) !important;
        }

        /* assistant answer text */
        .answer-body {
            font-size: 0.9rem;
            line-height: 1.7;
            color: var(--text-hi);
        }

        /* source box */
        .source-card {
            margin-top: 0.75rem;
            background: var(--bg-surface);
            border: 1px solid var(--border-mid);
            border-left: 3px solid var(--accent);
            border-radius: var(--radius-sm);
            padding: 0.6rem 0.85rem;
            font-size: 0.82rem;
            color: var(--text-mid);
            font-family: 'JetBrains Mono', monospace;
        }
        .source-card strong { color: var(--text-hi); }

        /* ══════════════════════════════════════
           CHAT INPUT
        ══════════════════════════════════════ */
        div[data-testid="stChatInput"] {
            background: var(--bg-raised) !important;
            border: 1px solid var(--border-mid) !important;
            border-radius: var(--radius-lg) !important;
            padding: 0.1rem 0.4rem !important;
        }
        div[data-testid="stChatInput"]:focus-within {
            border-color: rgba(108,138,255,0.45) !important;
            box-shadow: 0 0 0 3px var(--accent-dim) !important;
        }
        div[data-testid="stChatInput"] textarea {
            background: transparent !important;
            color: var(--text-hi) !important;
            font-size: 0.9rem !important;
            border: none !important;
        }
        div[data-testid="stChatInput"] textarea::placeholder {
            color: var(--text-lo) !important;
        }

        /* ══════════════════════════════════════
           SPINNER / ALERTS
        ══════════════════════════════════════ */
        .stSpinner > div { border-top-color: var(--accent) !important; }

        [data-testid="stAlert"] {
            background: var(--bg-raised) !important;
            border-color: var(--border-mid) !important;
            color: var(--text-mid) !important;
            border-radius: var(--radius-md) !important;
        }

        /* ══════════════════════════════════════
           SCROLLBAR
        ══════════════════════════════════════ */
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb {
            background: var(--border-mid);
            border-radius: 999px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "last_voice_signature" not in st.session_state:
    st.session_state.last_voice_signature = None

sample_questions = [
    "What is an Electronic Invoice?",
    "Is Electronic Invoicing mandatory?",
    "Is there any fee to be paid?",
    "In some months I have zero invoicing — is it still required?",
]


def transcribe_audio(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    get_gemini_api_key()
    client = genai.Client()
    suffix = Path(uploaded_file.name).suffix or ".mp3"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        temp_path = tmp.name
    try:
        mime_type = uploaded_file.type or "audio/wav"
        audio_file = client.files.upload(file=temp_path, config={"mime_type": mime_type})
        interaction = client.interactions.create(
            model="gemini-3.5-transcribe",
            input=[{"type": "audio", "uri": audio_file.uri, "mime_type": audio_file.mime_type}],
            generation_config={"transcription_config": {"language_codes": ["en-US"]}},
        )
        return (interaction.output_text or "").strip()
    finally:
        Path(temp_path).unlink(missing_ok=True)


def _strip_markdown(text: str) -> str:
    """Lightweight cleanup so TTS doesn't read asterisks or backticks."""
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"`{1,3}(.*?)`{1,3}", r"\1", text)
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
    text = re.sub(r"#{1,6}\s?", "", text)
    return text


def render_tts_button(text: str, element_id: str) -> None:
    """Embed a tiny HTML/JS component that toggles speech synthesis."""
    clean = _strip_markdown(text)
    tts_html = f"""
    <div style="margin-top:0.5rem;">
      <button id="{element_id}"
        style="background:#1a1e28; border:1px solid rgba(255,255,255,0.10);
               border-radius:8px; color:#8b90a0; cursor:pointer;
               font-size:0.9rem; padding:5px 10px; display:inline-flex; align-items:center; gap:6px;
               transition:all 0.15s ease; font-family:Inter,system-ui,sans-serif;"
        onmouseover="this.style.borderColor='rgba(255,255,255,0.16)'; this.style.color='#f0f2f8';"
        onmouseout="this.style.borderColor='rgba(255,255,255,0.10)'; this.style.color='#8b90a0';"
      >
        <span id="{element_id}_icon">🔊</span>
      </button>
    </div>
    <script>
    (function() {{
      const btn = document.getElementById('{element_id}');
      const icon = document.getElementById('{element_id}_icon');
      const label = document.getElementById('{element_id}_label');
      const text = {json.dumps(clean)};
      const synth = window.speechSynthesis;
      let utterance = new SpeechSynthesisUtterance(text);
      let isPlaying = false;
      let isPaused = false;

      utterance.onend = function() {{
        isPlaying = false; isPaused = false;
        icon.textContent = '🔊'; label.textContent = 'Listen';
      }};
      utterance.onerror = function() {{
        isPlaying = false; isPaused = false;
        icon.textContent = '🔊'; label.textContent = 'Listen';
      }};

      btn.addEventListener('click', function() {{
        if (!isPlaying && !isPaused) {{
          synth.cancel();               // stop any other speech first
          synth.speak(utterance);
          isPlaying = true; isPaused = false;
          icon.textContent = '⏸️'; label.textContent = 'Pause';
        }} else if (isPlaying) {{
          synth.pause();
          isPlaying = false; isPaused = true;
          icon.textContent = '▶️'; label.textContent = 'Resume';
        }} else if (isPaused) {{
          synth.resume();
          isPlaying = true; isPaused = false;
          icon.textContent = '⏸️'; label.textContent = 'Pause';
        }}
      }});
    }})();
    </script>
    """
    components.html(tts_html, height=55)


# ── SIDEBAR ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div class="brand-lockup">
            <div class="brand-icon">💬</div>
            <div>
                <div class="brand-name">FAQ Assistant</div>
                <div class="brand-sub">Grounded answers, instantly</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-section-title">Quick prompts</div>', unsafe_allow_html=True)
    for q in sample_questions:
        if st.button(q, use_container_width=True, key=f"prompt_{q[:20]}"):
            st.session_state.pending_question = q

    st.markdown('<div class="sidebar-section-title">Actions</div>', unsafe_allow_html=True)
    if st.button("↺  Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.rerun()

    st.markdown('<div class="sidebar-section-title">Voice input</div>', unsafe_allow_html=True)
    audio_recording = st.audio_input(
        "Record a voice message",
        sample_rate=16000,
        label_visibility="collapsed",
    )
    if audio_recording is not None:
        st.audio(audio_recording)
        try:
            voice_signature = hash(audio_recording.getvalue())
        except Exception:
            voice_signature = None

        if voice_signature and voice_signature != st.session_state.last_voice_signature:
            with st.spinner("Transcribing…"):
                try:
                    transcript = transcribe_audio(audio_recording)
                    if transcript:
                        st.session_state.pending_question = transcript
                        st.session_state.last_voice_signature = voice_signature
                        st.success("Transcribed — sent to chat")
                        st.rerun()
                    else:
                        st.warning("No speech detected.")
                except Exception as exc:
                    st.error(f"Transcription failed: {exc}")


# ── HERO ─────────────────────────────────────────────────────────────────
msg_count = len([m for m in st.session_state.messages if m["role"] == "user"])
st.markdown(
    f"""
    <div class="hero-wrap">
        <div class="hero-text">
            <h1 class="hero-title">Ask your <span>FAQ Assistant</span></h1>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ── CHAT HISTORY ─────────────────────────────────────────────────────────
for idx, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.markdown(
                f"<div class='answer-body'>{message['content']}</div>",
                unsafe_allow_html=True,
            )
            render_tts_button(message["content"], f"tts_{idx}")
        else:
            st.markdown(message["content"])


# ── INPUT HANDLING ────────────────────────────────────────────────────────
pending_question = st.session_state.pop("pending_question", None)
user_question = st.chat_input("Ask anything about the product…")
if pending_question and not user_question:
    user_question = pending_question

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown(
            "<div class='answer-body' style='color:var(--text-mid)'>Searching knowledge base…</div>",
            unsafe_allow_html=True,
        )
        with st.spinner(""):
            try:
                answer, sources = answer_question(user_question, st.session_state.history)
            except Exception as exc:
                answer = f"Something went wrong: {exc}"
                sources = []

        placeholder.markdown(
            f"<div class='answer-body'>{answer}</div>",
            unsafe_allow_html=True,
        )

        # TTS toggle for the newly generated answer
        render_tts_button(answer, f"tts_{len(st.session_state.messages)}")

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.history.append((user_question, answer))