from __future__ import annotations

from collections import deque

from google import genai

from src.config import get_chat_model, get_gemini_api_key
from src.retriever import format_chunks, retrieve

from functools import lru_cache

@lru_cache(maxsize=1)
def _get_client() -> genai.Client:
    get_gemini_api_key()
    return genai.Client()


SYSTEM_PROMPT = """You are an FAQ assistant.

Your job is to answer the user's question using ONLY the information
provided in the FAQ context.

Rules:
1. Do not invent information.
2. Do not use outside knowledge.
3. If the answer is not contained in the provided context, say that
   I'm sorry, the following query is out of my scope.
4. Give concise and clear answers.
5. Preserve important details such as numbers, dates, URLs, email
   addresses, and instructions.
6. If the context contains multiple relevant pieces of information,
   combine them into one coherent answer.
7. Do not mention internal retrieval, embeddings, vector databases,
   or RAG unless the user explicitly asks about the system.
8. If user gives a greeting, greet back, but any other out of context query should not be catered.
"""

def answer_question(question: str, history: list[tuple[str, str]] | None = None) -> tuple[str, list]:
    chunks = retrieve(question, top_k=3)
    if not chunks:
        return "I couldn't find this information in the FAQ document.", []

    if chunks[0].score > 1.2:
        return "I couldn't find this information in the FAQ document.", []

    context = format_chunks(chunks)
    get_gemini_api_key()
    client = _get_client()

    conversation = ""
    if history:
        recent = history[-5:]
        conversation = "\n".join(
            f"User: {user}\nAssistant: {assistant}" for user, assistant in recent
        )

    if conversation:
        history_block = f"CONVERSATION HISTORY:\n{conversation}\n\n"
    else:
        history_block = ""

    user_input = f"""FAQ CONTEXT:

{context}

{history_block}
USER QUESTION:

{question}
"""

    response = client.models.generate_content(
        model=get_chat_model(),
        contents=user_input,
        config={"system_instruction": SYSTEM_PROMPT},
    )
    return (response.text or "").strip(), [chunk.metadata for chunk in chunks]


def run_cli() -> None:
    print("=" * 33)
    print("        FAQ RAG CHATBOT")
    print("=" * 33)
    print("\nAsk a question or type 'exit' to quit.\n")

    history = deque(maxlen=10)
    while True:
        question = input("You: ").strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        try:
            answer, _sources = answer_question(question, list(history))
        except Exception as exc:
            answer = f"Error: {exc}"

        print(f"\nAssistant: {answer}\n")
        history.append((question, answer))


if __name__ == "__main__":
    run_cli()
