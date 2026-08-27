from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_PDF_PATH = DATA_DIR / "document.pdf"
VECTOR_STORE_DIR = BASE_DIR / "vectorstore"
CHROMA_COLLECTION_NAME = "faq_documents"

load_dotenv(BASE_DIR / ".env")


def get_env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value.strip() == "":
        raise ValueError(f"{name} is not configured.")
    return value


def get_openai_api_key() -> str:
    return get_env("OPENAI_API_KEY")


def get_gemini_api_key() -> str:
    return get_env("GEMINI_API_KEY")


def get_pdf_path() -> Path:
    pdf_path = Path(os.getenv("FAQ_PDF_PATH", str(DEFAULT_PDF_PATH)))
    if not pdf_path.is_absolute():
        pdf_path = BASE_DIR / pdf_path
    return pdf_path


def get_chat_model() -> str:
    return os.getenv("GEMINI_CHAT_MODEL", "gemini-3.5-flash")


def get_embedding_model() -> str:
    return os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2")


def get_vector_store_dir() -> Path:
    path = Path(os.getenv("VECTOR_STORE_DIR", str(VECTOR_STORE_DIR)))
    if not path.is_absolute():
        path = BASE_DIR / path
    return path
