from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import time

import chromadb
import pymupdf
from google import genai

from config import (
    CHROMA_COLLECTION_NAME,
    get_embedding_model,
    get_gemini_api_key,
    get_pdf_path,
    get_vector_store_dir,
)


@dataclass
class Chunk:
    chunk_id: str
    text: str
    page: int


def clean_text(text: str) -> str:
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pages(pdf_path: Path) -> list[tuple[int, str]]:
    if not pdf_path.exists():
        raise FileNotFoundError(f"FAQ PDF could not be found at: {pdf_path}")

    pages: list[tuple[int, str]] = []
    with pymupdf.open(pdf_path) as doc:
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text", sort=True)
            pages.append((i, clean_text(text)))
    return pages


def chunk_text(page_text: str, page_number: int) -> list[Chunk]:
    if not page_text:
        return []

    blocks = [b.strip() for b in re.split(r"\n\s*\n", page_text) if b.strip()]
    chunks: list[Chunk] = []
    for index, block in enumerate(blocks, start=1):
        chunks.append(Chunk(chunk_id=f"p{page_number}_c{index}", text=block, page=page_number))
    return chunks


def build_chunks(pages: Iterable[tuple[int, str]]) -> list[Chunk]:
    chunks: list[Chunk] = []
    for page_number, text in pages:
        chunks.extend(chunk_text(text, page_number))
    return chunks


def get_gemini_client() -> genai.Client:
    get_gemini_api_key()
    return genai.Client()


def get_collection():
    vector_store_dir = get_vector_store_dir()
    vector_store_dir.mkdir(parents=True, exist_ok=True)
    chroma_client = chromadb.PersistentClient(path=str(vector_store_dir))
    return chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)

def embed_texts(client: genai.Client, texts: list[str]) -> list[list[float]]:
    embeddings: list[list[float]] = []
    batch_size = 90  # stay safely under the 100/min limit
    
    for i, text in enumerate(texts):
        response = client.models.embed_content(model=get_embedding_model(), contents=text)
        embeddings.append(list(response.embeddings[0].values))
        
        # After every batch_size requests, pause for 65 seconds
        if (i + 1) % batch_size == 0:
            remaining = len(texts) - (i + 1)
            if remaining > 0:
                print(f"Rate limit pause after {i + 1} embeddings ({remaining} remaining)...")
                time.sleep(65)
    
    return embeddings


def ingest() -> None:
    pdf_path = get_pdf_path()
    pages = extract_pages(pdf_path)
    chunks = build_chunks(pages)

    if not chunks:
        raise ValueError("The PDF does not appear to contain extractable text.")

    print(f"Extracted {len(pages)} pages")
    for page_number, text in pages[:3]:
        print(f"\n--- Page {page_number} ---\n{text[:1000]}")

    print(f"\nTotal chunks: {len(chunks)}")
    for chunk in chunks[:3]:
        print(f"\n--- {chunk.chunk_id} (page {chunk.page}) ---\n{chunk.text[:1000]}")

    client = get_gemini_client()
    vector_store_dir = get_vector_store_dir()
    chroma_client = chromadb.PersistentClient(path=str(vector_store_dir))
    try:
        chroma_client.delete_collection(CHROMA_COLLECTION_NAME)
    except Exception:
        pass
    collection = chroma_client.get_or_create_collection(name=CHROMA_COLLECTION_NAME)

    embeddings = embed_texts(client, [chunk.text for chunk in chunks])
    collection.add(
        ids=[chunk.chunk_id for chunk in chunks],
        documents=[chunk.text for chunk in chunks],
        embeddings=embeddings,
        metadatas=[{"source": pdf_path.name, "page": chunk.page} for chunk in chunks],
    )

    print("\nIngestion complete.")


if __name__ == "__main__":
    ingest()
