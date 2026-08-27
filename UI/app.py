from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.chatbot import answer_question  # noqa: E402


st.set_page_config(
    page_title="FAQ RAG Chatbot",
    page_icon="💬",
    layout="centered",
)


st.markdown(
    """
    <style>
        .stApp {
            background: linear-gradient(180deg, #f7f9fc 0%, #eef3f8 100%);
        }
        .chat-title {
            font-size: 2.1rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }
        .chat-subtitle {
            color: #4b5563;
            margin-top: 0;
            margin-bottom: 1.25rem;
        }
        .source-box {
            background: rgba(255,255,255,0.8);
            border: 1px solid rgba(148,163,184,0.35);
            border-radius: 14px;
            padding: 0.8rem 1rem;
            margin-top: 0.5rem;
            font-size: 0.92rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


st.markdown('<div class="chat-title">FAQ RAG Chatbot</div>', unsafe_allow_html=True)
st.markdown(
    '<p class="chat-subtitle">Ask questions about the FAQ document and get grounded answers.</p>',
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "history" not in st.session_state:
    st.session_state.history = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sources", expanded=False):
                for source in message["sources"]:
                    st.markdown(
                        f"<div class='source-box'>Source: {source.get('source', 'unknown')} | "
                        f"Page: {source.get('page', '?')}</div>",
                        unsafe_allow_html=True,
                    )


user_question = st.chat_input("Type your question here...")

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})
    with st.chat_message("user"):
        st.markdown(user_question)

    with st.chat_message("assistant"):
        with st.spinner("Searching the FAQ and drafting an answer..."):
            try:
                answer, sources = answer_question(user_question, st.session_state.history)
            except Exception as exc:
                answer = f"Error: {exc}"
                sources = []

        st.markdown(answer)
        if sources:
            with st.expander("Sources", expanded=True):
                for source in sources:
                    st.markdown(
                        f"<div class='source-box'>Source: {source.get('source', 'unknown')} | "
                        f"Page: {source.get('page', '?')}</div>",
                        unsafe_allow_html=True,
                    )

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )
    st.session_state.history.append((user_question, answer))

