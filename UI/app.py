from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import streamlit as st
from google import genai


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.chatbot import answer_question  # noqa: E402
from src.config import get_gemini_api_key  # noqa: E402


st.set_page_config(
    page_title="HELPLINE CHATBOT FOR FAQ",
    page_icon="💬",
    layout="wide",
)


st.markdown(
    """
    <style>
        :root {
            --bg: #f3f5f8;
            --panel: rgba(255, 255, 255, 0.82);
            --panel-strong: rgba(255, 255, 255, 0.94);
            --border: rgba(15, 23, 42, 0.08);
            --text: #0f172a;
            --muted: #475569;
            --accent: #2563eb;
            --accent-2: #0f766e;
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(37, 99, 235, 0.16), transparent 30%),
                radial-gradient(circle at top right, rgba(15, 118, 110, 0.12), transparent 28%),
                linear-gradient(180deg, #f8fafc 0%, #edf2f7 100%);
            color: var(--text);
        }
        .hero {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.98), rgba(37, 99, 235, 0.92));
            color: white;
            border-radius: 24px;
            padding: 28px 30px;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.16);
            margin-bottom: 1rem;
        }
        .hero h1 {
            margin: 0;
            font-size: 2.2rem;
            line-height: 1.05;
        }
        .hero p {
            margin: 0.65rem 0 0 0;
            color: rgba(255, 255, 255, 0.82);
            max-width: 62ch;
        }
        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        .pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.4rem 0.75rem;
            border-radius: 999px;
            background: rgba(255,255,255,0.12);
            border: 1px solid rgba(255,255,255,0.14);
            font-size: 0.86rem;
            color: rgba(255,255,255,0.92);
        }
        .panel {
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 1rem 1rem 0.5rem 1rem;
            box-shadow: 0 14px 35px rgba(15, 23, 42, 0.05);
            backdrop-filter: blur(10px);
        }
        .side-card {
            background: var(--panel-strong);
            border: 1px solid var(--border);
            border-radius: 18px;
            padding: 1rem;
            margin-bottom: 0.9rem;
            box-shadow: 0 12px 28px rgba(15, 23, 42, 0.05);
        }
        .side-title {
            font-weight: 750;
            margin-bottom: 0.35rem;
            font-size: 1rem;
            color: black;
        }
        .side-text {
            color: var(--muted);
            font-size: 0.92rem;
            line-height: 1.5;
        }
        .source-box {
            background: #f8fafc;
            border: 1px solid rgba(148,163,184,0.28);
            border-radius: 14px;
            padding: 0.72rem 0.9rem;
            margin-top: 0.5rem;
            font-size: 0.92rem;
            color: #111827;
        }
        .source-box strong {
            color: #000000;
        }
        .assistant-answer {
            color: #000000;
        }
        .stChatMessage {
            border-radius: 18px;
        }
        .stButton > button {
            border-radius: 999px;
            border: 1px solid rgba(37, 99, 235, 0.18);
            font-weight: 600;
            padding: 0.55rem 0.9rem;
        }
        .stButton > button:hover {
            border-color: rgba(37, 99, 235, 0.42);
            color: var(--accent);
        }
        div[data-testid="stChatInput"] textarea {
            border-radius: 16px !important;
            color: white !important;
        }
        .mini-stat {
            background: linear-gradient(135deg, rgba(37,99,235,0.1), rgba(15,118,110,0.08));
            border: 1px solid rgba(37,99,235,0.12);
            border-radius: 16px;
            padding: 0.8rem 0.9rem;
            margin-bottom: 0.65rem;
        }
        .mini-stat strong {
            display: block;
            font-size: 1.15rem;
        }
        .mini-stat span {
            color: var(--muted);
            font-size: 0.9rem;
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
    "In some months I have Zero invoicing, is it still required for me?",
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
            input=[
                {
                    "type": "audio",
                    "uri": audio_file.uri,
                    "mime_type": audio_file.mime_type,
                }
            ],
            generation_config={
                "transcription_config": {
                    "language_codes": ["en-US"],
                }
            },
        )
        transcript = (interaction.output_text or "").strip()
        return transcript
    finally:
        Path(temp_path).unlink(missing_ok=True)


with st.sidebar:
    st.markdown(
        """
        <div class="side-card">
            <div class="side-title">FAQ ChatboT Demo</div>
            <div class="side-text">
                A simple demo chatbot for your product FAQ. Ask a question,
                get a grounded answer.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("### Quick Prompts")
    for q in sample_questions:
        if st.button(q, use_container_width=True):
            st.session_state.pending_question = q

    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.rerun()

    st.markdown("### Speech Input")
    audio_recording = st.audio_input(
        "Record a voice message",
        sample_rate=16000,
        label_visibility="collapsed",
    )
    if audio_recording is not None:
        st.audio(audio_recording)
        voice_signature = None
        try:
            voice_signature = hash(audio_recording.getvalue())
        except Exception:
            pass

        if voice_signature is not None and voice_signature != st.session_state.last_voice_signature:
            with st.spinner("Transcribing audio..."):
                try:
                    transcript = transcribe_audio(audio_recording)
                    if transcript:
                        st.session_state.pending_question = transcript
                        st.session_state.last_voice_signature = voice_signature
                        st.success("Voice input transcribed and loaded into chat.")
                        st.rerun()
                    else:
                        st.warning("No speech was detected in the recording.")
                except Exception as exc:
                    st.error(f"Transcription failed: {exc}")


st.markdown(
    """
    <div class="hero">
        <h1>FAQ Demo</h1>
        <p>
            A demo chatbot for product FAQ lookups. Ask your questions right away.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# st.markdown('<div class="panel">', unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            st.markdown(
                f"<div class='assistant-answer'>{message['content']}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(message["content"])

pending_question = st.session_state.pop("pending_question", None)
user_question = st.chat_input("Ask about the Product...")
if pending_question and not user_question:
    user_question = pending_question

if user_question:
    # Store user message
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    # Generate and display assistant answer (NOT indented inside user block)
    with st.chat_message("assistant"):
        assistant_placeholder = st.empty()
        assistant_placeholder.markdown("<div class='assistant-answer'>Searching...</div>", unsafe_allow_html=True)
        with st.spinner(""):
            try:
                answer, sources = answer_question(user_question, st.session_state.history)
            except Exception as exc:
                answer = f"Error: {exc}"
                sources = []

        assistant_placeholder.markdown(f"<div class='assistant-answer'>{answer}</div>", unsafe_allow_html=True)

    # Persist the assistant answer so it survives reruns
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.history.append((user_question, answer))