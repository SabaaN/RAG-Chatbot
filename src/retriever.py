from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import chromadb
from google import genai

from src.config import CHROMA_COLLECTION_NAME, get_embedding_model, get_gemini_api_key, get_vector_store_dir


@dataclass
class RetrievedChunk:
    text: str
    score: float
    metadata: dict[str, Any]


def get_gemini_client() -> genai.Client:
    get_gemini_api_key()
    return genai.Client()


def get_collection():
    chroma_client = chromadb.PersistentClient(path=str(get_vector_store_dir()))
    return chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)


def retrieve(question: str, top_k: int = 5) -> list[RetrievedChunk]:
    client = get_gemini_client()
    collection = get_collection()

    query_response = client.models.embed_content(model=get_embedding_model(), contents=question)
    query_embedding = list(query_response.embeddings[0].values)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    chunks: list[RetrievedChunk] = []
    for text, metadata, distance in zip(documents, metadatas, distances):
        chunks.append(RetrievedChunk(text=text, metadata=metadata or {}, score=float(distance)))
    return chunks


def format_chunks(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(
        f"[Source: {chunk.metadata.get('source', 'unknown')}, page {chunk.metadata.get('page', '?')}]\n{chunk.text}"
        for chunk in chunks
    )
