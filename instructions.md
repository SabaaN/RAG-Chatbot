# RAG FAQ Chatbot — Instructions

## 1. Project Goal

Build a Retrieval-Augmented Generation (RAG) chatbot that answers questions using information contained in an existing FAQ PDF document.

The chatbot must:

- Read the FAQ PDF from the project directory.
- Extract and clean its text.
- Split the document into meaningful chunks.
- Generate embeddings for each chunk using the OpenAI API.
- Store the embeddings in a local vector database.
- Retrieve the most relevant chunks for each user question.
- Send the retrieved context to an OpenAI language model.
- Generate an answer based only on the retrieved FAQ information.
- Clearly state when the answer cannot be found in the FAQ.
- Provide a simple conversational interface.

The OpenAI API will be used for both embeddings and answer generation.

---

# 2. Recommended Project Structure

Create the following project structure:

```text
faq-rag-chatbot/
│
├── data/
│   └── faq.pdf
│
├── vectorstore/
│   └── ...
│
├── src/
│   ├── __init__.py
│   ├── ingest.py
│   ├── retrieve.py
│   ├── chatbot.py
│   └── config.py
│
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── instructions.md
```

Place the existing FAQ PDF at:

```text
data/faq.pdf
```

If the PDF has a different filename, update the path in the ingestion script.

---

# 3. Technology Stack

Use:

- Python 3.10+
- OpenAI Python SDK
- PyMuPDF for PDF extraction
- ChromaDB for local vector storage
- NumPy for vector calculations if needed
- python-dotenv for environment variables

Do not use a hosted vector database for the initial implementation.

The goal is to keep the project simple and runnable locally.

---

# 4. Install Dependencies

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

### Windows

```bash
.venv\Scripts\activate
```

### Linux/macOS

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install openai pymupdf chromadb python-dotenv
```

Create `requirements.txt`:

```text
openai
pymupdf
chromadb
python-dotenv
```

---

# 5. Configure the OpenAI API Key

Create a `.env` file:

```env
OPENAI_API_KEY=your_api_key_here
```

Never hard-code the API key inside Python files.

Add `.env` to `.gitignore`:

```text
.env
.venv/
__pycache__/
vectorstore/
```

The OpenAI API is accessed through the official OpenAI platform.

---

# 6. PDF Ingestion Pipeline

Create:

```text
src/ingest.py
```

This script is responsible for:

1. Opening the PDF.
2. Extracting text from every page.
3. Cleaning the extracted text.
4. Splitting the text into chunks.
5. Generating embeddings.
6. Storing the chunks and embeddings in ChromaDB.

Use PyMuPDF for extraction.

Basic extraction:

```python
import pymupdf

doc = pymupdf.open("data/faq.pdf")

for page in doc:
    text = page.get_text("text", sort=True)
    print(text)
```

`sort=True` can help produce a more natural top-left-to-bottom-right reading order for PDFs whose internal text ordering is unusual.

---

# 7. Text Cleaning

Create a cleaning function.

The cleaning process should:

- Remove excessive whitespace.
- Remove repeated blank lines.
- Normalize line breaks.
- Preserve headings.
- Preserve FAQ questions.
- Preserve FAQ answers.
- Avoid aggressively removing punctuation.
- Preserve important numbers, URLs, email addresses, and special terminology.

Example:

```python
import re

def clean_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()
```

Do not remove question/answer formatting if the PDF contains structures such as:

```text
Q: How do I reset my password?

A: Go to the settings page...
```

This structure is useful for retrieval.

---

# 8. Chunking Strategy

Do not embed the entire PDF as one document.

Split it into smaller chunks.

For an FAQ document, prefer semantic chunks over arbitrary character splits.

A good starting configuration is:

```text
Chunk size: approximately 500–800 tokens
Chunk overlap: approximately 50–100 tokens
```

However, FAQ documents should ideally preserve complete question/answer pairs.

For example, prefer:

```text
Question:
How can I reset my password?

Answer:
Go to Settings > Security > Reset Password...
```

as one chunk rather than splitting the question from the answer.

Each chunk should contain metadata such as:

```python
{
    "source": "faq.pdf",
    "page": 4,
    "chunk_id": 17
}
```

This will allow the chatbot to identify where an answer came from.

---

# 9. Generate Embeddings

Use an OpenAI embedding model.

For example:

```python
from openai import OpenAI

client = OpenAI()

response = client.embeddings.create(
    model="text-embedding-3-small",
    input="Example FAQ question and answer"
)

embedding = response.data[0].embedding
```

The embedding represents the semantic meaning of the FAQ chunk as a numerical vector.

The same embedding model must be used when:

- Creating the document embeddings.
- Embedding the user's question.

---

# 10. Store Embeddings in ChromaDB

Create a persistent ChromaDB collection.

Example:

```python
import chromadb

chroma_client = chromadb.PersistentClient(
    path="./vectorstore"
)

collection = chroma_client.get_or_create_collection(
    name="faq_documents"
)
```

Each document chunk should have:

- A unique ID.
- The original text.
- Its embedding.
- Metadata.

Example:

```python
collection.add(
    ids=["chunk_001"],
    documents=["How can I reset my password? ..."],
    embeddings=[embedding],
    metadatas=[
        {
            "source": "faq.pdf",
            "page": 4
        }
    ]
)
```

The ingestion script should be safe to run multiple times.

Ideally, either:

- Clear and rebuild the collection, or
- Detect that the document has already been indexed.

For this first version, rebuilding the collection is acceptable.

---

# 11. Retrieval

Create:

```text
src/retrieve.py
```

The retrieval process should:

1. Receive the user's question.
2. Generate an embedding for the question.
3. Search ChromaDB.
4. Retrieve the most relevant FAQ chunks.
5. Return those chunks to the chatbot.

Example:

```python
question = "How can I change my password?"

response = client.embeddings.create(
    model="text-embedding-3-small",
    input=question
)

query_embedding = response.data[0].embedding

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=5
)
```

Start with:

```text
top_k = 5
```

Then tune it based on retrieval quality.

---

# 12. Retrieval Threshold

Do not blindly provide the nearest chunks to the LLM.

The chatbot should avoid answering from unrelated FAQ content.

Implement a relevance check.

If the retrieved documents are not sufficiently relevant, return:

```text
I couldn't find this information in the FAQ document.
```

The exact threshold will depend on the embedding/vector database configuration, so test several questions and inspect the retrieval results before choosing a threshold.

---

# 13. Generate the Final Answer

Create:

```text
src/chatbot.py
```

The chatbot should send the retrieved FAQ context to an OpenAI language model.

The prompt should enforce strict grounding.

Use a system instruction similar to:

```text
You are an FAQ assistant.

Your job is to answer the user's question using ONLY the information
provided in the FAQ context.

Rules:

1. Do not invent information.
2. Do not use outside knowledge.
3. If the answer is not contained in the provided context, say that
   the information was not found in the FAQ.
4. Give concise and clear answers.
5. Preserve important details such as numbers, dates, URLs, email
   addresses, and instructions.
6. If the context contains multiple relevant pieces of information,
   combine them into one coherent answer.
7. Do not mention internal retrieval, embeddings, vector databases,
   or RAG unless the user explicitly asks about the system.
```

Then provide the retrieved context:

```text
FAQ CONTEXT:

[Chunk 1]
...

[Chunk 2]
...

[Chunk 3]
...

USER QUESTION:

How can I change my password?
```

The model should answer using the context.

---

# 14. OpenAI Response Generation

Use the current OpenAI Python SDK.

Example structure:

```python
from openai import OpenAI

client = OpenAI()

response = client.responses.create(
    model="gpt-5-mini",
    instructions="""You are an FAQ assistant.

Answer the user's question only using the supplied FAQ context.

If the answer cannot be found in the context, say:
"I couldn't find this information in the FAQ document."

Do not invent information.
""",
    input=f"""
FAQ CONTEXT:

{context}

USER QUESTION:

{question}
"""
)

answer = response.output_text
```

If a different currently available OpenAI model is preferred for the project, make the model configurable through `.env` rather than hard-coding it.

For example:

```env
OPENAI_CHAT_MODEL=gpt-5-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

Then load the values using `python-dotenv`.

---

# 15. Conversation History

The chatbot should support follow-up questions.

For example:

```text
User:
How do I reset my password?

Assistant:
Go to Settings > Security...

User:
What if I don't have access to my email?

Assistant:
...
```

The second question may depend on the first message.

Maintain a small conversation history:

```python
conversation_history = []
```

Add each user question and assistant answer to the history.

However, do not send an unlimited conversation history.

Keep the last few turns, for example:

```text
last 5–10 messages
```

The retrieved FAQ context should remain the primary source of truth.

---

# 16. Query Rewriting for Follow-Up Questions

For better retrieval, consider rewriting follow-up questions.

Example:

```text
Previous:
How do I reset my password?

Current:
What if I don't receive it?
```

The retrieval query should become something like:

```text
What should I do if I don't receive the password reset email?
```

This can significantly improve retrieval for conversational questions.

Implement this only after the basic RAG pipeline works.

Do not overcomplicate the first version.

---

# 17. Chat Interface

Start with a terminal chatbot.

Example:

```text
=================================
        FAQ RAG CHATBOT
=================================

Ask a question or type 'exit' to quit.

You: How do I reset my password?

Assistant: You can reset your password by...

You: How long does it take?

Assistant: According to the FAQ...

You: exit

Goodbye!
```

The terminal interface is sufficient for the initial implementation.

After the RAG pipeline works correctly, optionally create a web UI using Streamlit.

---

# 18. Optional Streamlit Interface

If a browser-based interface is desired, install:

```bash
pip install streamlit
```

Create:

```text
app.py
```

The UI should contain:

- Chat history.
- Text input.
- Send button.
- Assistant responses.
- Optional source/page information.

Run:

```bash
streamlit run app.py
```

---

# 19. Source Citations

The chatbot should ideally tell the user where the answer came from.

Since each chunk has metadata:

```python
{
    "source": "faq.pdf",
    "page": 4
}
```

The answer can display:

```text
According to the FAQ, you can reset your password from
Settings > Security.

Source: FAQ PDF, page 4
```

Do not expose the raw vector database information.

---

# 20. Error Handling

Handle the following cases:

### Missing PDF

```text
FileNotFoundError:
FAQ PDF could not be found.
```

### Empty PDF

If no text can be extracted:

```text
The PDF does not appear to contain extractable text.
```

### Missing API key

```text
OPENAI_API_KEY is not configured.
```

### OpenAI API error

Catch API exceptions and show a useful error instead of crashing.

### Empty user question

Ignore empty input.

### No relevant results

Return:

```text
I couldn't find this information in the FAQ document.
```

---

# 21. Important: Scanned PDFs

Before implementing the chatbot, determine whether the FAQ PDF contains actual text or scanned images.

PyMuPDF can extract text directly from normal text-based PDFs.

If:

```python
page.get_text("text")
```

returns almost nothing even though the PDF visibly contains text, the PDF is probably scanned/image-based.

In that case, add an OCR pipeline.

Do not implement OCR unless it is actually necessary.

For the first version:

```text
Text PDF → PyMuPDF
Scanned PDF → OCR fallback
```

---

# 22. Testing the RAG System

Create a test set containing at least 15–30 questions.

Divide them into:

### Questions directly answered by the FAQ

Example:

```text
What is the refund policy?
```

### Questions requiring multiple FAQ sections

Example:

```text
Can I cancel my subscription and still receive a refund?
```

### Paraphrased questions

FAQ:

```text
How can I change my password?
```

User:

```text
I forgot my password. What do I need to do?
```

### Questions not answered by the FAQ

Example:

```text
What is the weather today?
```

The chatbot should refuse to answer from outside knowledge.

### Ambiguous questions

Example:

```text
How long does it take?
```

The chatbot should use conversation history if possible, or ask for clarification.

---

# 23. Evaluate Retrieval Separately From Generation

Do not only evaluate the final chatbot response.

Test retrieval independently.

For every question, inspect:

```text
QUESTION
↓
QUERY EMBEDDING
↓
TOP 5 CHUNKS
↓
ARE THE CORRECT CHUNKS PRESENT?
↓
LLM ANSWER
```

If the correct FAQ information is not retrieved, changing the LLM will not solve the underlying problem.

Improve:

- Chunk size.
- Chunk overlap.
- Metadata.
- Query rewriting.
- `top_k`.
- Retrieval threshold.

before changing the generation model.

---

# 24. Recommended Initial Architecture

Use this architecture:

```text
                 ┌─────────────────┐
                 │     FAQ PDF     │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │    PyMuPDF      │
                 │  Text Extract   │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Cleaning +      │
                 │ Chunking        │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ OpenAI          │
                 │ Embeddings      │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │   ChromaDB      │
                 │ Vector Store    │
                 └────────┬────────┘
                          │
                          │
User Question ────────────┤
                          ▼
                 ┌─────────────────┐
                 │ Query Embedding │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Similarity      │
                 │ Search          │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Relevant FAQ    │
                 │ Context         │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ OpenAI LLM      │
                 │ Generation      │
                 └────────┬────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Final Answer    │
                 └─────────────────┘
```

---

# 25. Implementation Order

Do not build everything simultaneously.

Implement the project in this order:

### Phase 1 — PDF extraction

Create:

```text
src/ingest.py
```

Verify that the FAQ PDF is being extracted correctly.

Run:

```bash
python src/ingest.py
```

Print several extracted pages and inspect them manually.

---

### Phase 2 — Chunking

Implement chunking.

Print:

```text
Total chunks: 42

Chunk 1:
...

Chunk 2:
...
```

Verify that FAQ questions and their answers are not unnecessarily separated.

---

### Phase 3 — Embeddings

Add OpenAI embeddings.

Verify that embeddings are being generated successfully.

Do not commit your API key.

---

### Phase 4 — ChromaDB

Store the chunks and embeddings.

Verify that the vector database persists inside:

```text
vectorstore/
```

---

### Phase 5 — Retrieval

Create:

```text
src/retrieve.py
```

Test:

```text
Question:
How do I reset my password?

Retrieved chunks:
1. ...
2. ...
3. ...
```

Make sure the correct FAQ entry appears near the top.

---

### Phase 6 — Generation

Connect retrieval to the OpenAI LLM.

Pipeline:

```text
Question
   ↓
Embedding
   ↓
Vector Search
   ↓
Top 5 FAQ chunks
   ↓
Prompt
   ↓
OpenAI
   ↓
Answer
```

---

### Phase 7 — Conversation

Add conversation history.

Test follow-up questions.

---

### Phase 8 — UI

Only after the RAG pipeline works correctly, build the Streamlit interface.

---

# 26. Final Files

The completed project should contain approximately:

```text
faq-rag-chatbot/
│
├── data/
│   └── faq.pdf
│
├── vectorstore/
│
├── src/
│   ├── __init__.py
│   ├── ingest.py
│   ├── retrieve.py
│   ├── chatbot.py
│   └── config.py
│
├── app.py
├── .env
├── .gitignore
├── requirements.txt
├── README.md
└── instructions.md
```

---

# 27. Definition of Done

The project is considered complete when:

- [ ] The PDF is successfully loaded.
- [ ] Text is correctly extracted.
- [ ] FAQ content is chunked appropriately.
- [ ] OpenAI embeddings are generated.
- [ ] ChromaDB stores the embeddings.
- [ ] User questions are embedded.
- [ ] Relevant FAQ chunks are retrieved.
- [ ] The OpenAI model generates answers from retrieved context.
- [ ] The chatbot refuses to invent answers.
- [ ] Questions outside the FAQ are handled appropriately.
- [ ] Follow-up questions work reasonably well.
- [ ] API keys are stored in `.env`.
- [ ] `.env` is excluded from Git.
- [ ] The project can be run locally from a clean environment.
- [ ] Retrieval has been manually tested with at least 15–30 questions.
- [ ] The optional Streamlit UI works.

---

# 28. Important Design Principle

The most important principle of this project is:

> **Retrieval quality comes before generation quality.**

Do not attempt to solve poor retrieval by simply using a more powerful LLM.

The system should first retrieve the correct FAQ information. The LLM's job is primarily to turn that retrieved information into a natural answer.

A good RAG pipeline should behave like:

```text
User Question
      ↓
Find relevant FAQ information
      ↓
Give that information to the LLM
      ↓
Generate a grounded answer
```

rather than:

```text
User Question
      ↓
LLM guesses an answer
```

---

# 29. Suggested Future Improvements

Once the basic implementation works, consider adding:

1. Hybrid search — keyword + semantic search.
2. Reranking of retrieved chunks.
3. Query rewriting.
4. Better FAQ-specific chunking.
5. Conversation-aware retrieval.
6. Source citations.
7. Confidence/relevance scoring.
8. Streaming responses.
9. Streamlit UI.
10. Automated RAG evaluation.
11. Multiple PDF support.
12. Document upload functionality.
13. Authentication.
14. Logging and monitoring.
15. Production vector database.

Do not implement these initially.

First get the basic:

```text
PDF → Embeddings → ChromaDB → Retrieval → OpenAI → Answer
```

pipeline working reliably.
