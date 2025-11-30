
#  LAB 8 — Build a Production RAG API (FastAPI + Databricks Model Serving)

##  Learning Objectives

By the end of this lab, learners will:

* Build a **REST API** for RAG using FastAPI
* Call **Databricks Model Serving** for embeddings (and optionally LLM)
* Perform **semantic retrieval** against precomputed embeddings
* Construct a **RAG prompt** and send it to an LLM endpoint
* Return a JSON response suitable for real applications

---

##  1. Target Architecture

High-level flow:

```text
Client → FastAPI RAG API → Databricks Serving (Embeddings + LLM) → Answer
                            ↑
                            └── Precomputed vector store (chunks + embeddings)
```

* **FastAPI**: Exposes `/rag/query` for clients
* **Databricks Serving**:

  * Endpoint 1 → Embedding model (e.g., `rag_embedder_endpoint`)
  * Endpoint 2 → LLM (e.g., `dbrx_instruct_endpoint` or similar)
* **Vector Store**:

  * Precomputed `chunks` and `embeddings` from earlier labs (stored as `.npy` / `.json` / DB export)

For the lab, we’ll assume you exported `chunks` and `embeddings` into simple files.

---

## 2. Prerequisites (Environment Setup)

Run these in your terminal or in a Databricks `%pip` cell if you’re building locally:

```bash
pip install fastapi uvicorn[standard] requests python-dotenv numpy
```

If running from a Databricks notebook, install:

```python
%pip install fastapi uvicorn[standard] requests python-dotenv numpy
dbutils.library.restartPython()
```

---

## 3. Configure Databricks Model Serving

You need:

* A **Serving endpoint** for embeddings (from MLflow model in Lab 5), e.g.:

  * Name: `rag_embedder_endpoint`

* Optionally, a **Serving endpoint** for LLM (DBRX or similar), e.g.:

  * Name: `dbrx_instruct_endpoint`

In the workspace UI for each endpoint, note the **“REST URL”**.

Example (placeholder):

```text
https://<your-workspace>/serving-endpoints/rag_embedder_endpoint/invocations
https://<your-workspace>/serving-endpoints/dbrx_instruct_endpoint/invocations
```

Create a `.env` file next to your `app.py`:

```env
DATABRICKS_HOST=https://<your-workspace-url>         # without trailing slash
DATABRICKS_TOKEN=YOUR_PERSONAL_ACCESS_TOKEN
EMBED_ENDPOINT=/serving-endpoints/rag_embedder_endpoint/invocations
LLM_ENDPOINT=/serving-endpoints/dbrx_instruct_endpoint/invocations
TOP_K=3
```

---

## 4. Prepare Vector Data (Chunks + Embeddings)

From Databricks (Notebook), export your prepared chunks + embeddings into files the API can load.

Example in Databricks notebook:

```python
import numpy as np

df = spark.read.format("delta").load("/Volumes/workspace/lab/myvolume/prepared_chunks")

# Assume schema: chunk (string), embedding (array<float>)
pdf = df.toPandas()

chunks = pdf["chunk"].tolist()
embeddings = np.stack(pdf["embedding"].values).astype("float32")

np.save("/dbfs/FileStore/rag/chunks.npy", np.array(chunks, dtype=object))
np.save("/dbfs/FileStore/rag/embeddings.npy", embeddings)
```

Then download from DBFS (e.g. via UI) to the machine where FastAPI will run, and place them in a `data/` folder:

```text
rag_api/
  app.py
  data/
    chunks.npy
    embeddings.npy
```

---

##  5. Implement Databricks Client (Embedding + LLM Calls)

Create `dbx_client.py` (or just put this directly in `app.py` if you want to keep it simpler):

```python
# dbx_client.py
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")
EMBED_ENDPOINT = os.getenv("EMBED_ENDPOINT")   # path part
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT")

HEADERS = {
    "Authorization": f"Bearer {DATABRICKS_TOKEN}",
    "Content-Type": "application/json"
}

def call_embedding_endpoint(texts):
    """
    texts: list[str]
    returns: list[embedding_vectors]
    """
    url = f"{DATABRICKS_HOST}{EMBED_ENDPOINT}"

    payload = {"inputs": texts}

    resp = requests.post(url, headers=HEADERS, data=json.dumps(payload))
    resp.raise_for_status()
    data = resp.json()

    # expect format: {"predictions": [[...], [...]]}
    return data["predictions"]

def call_llm(prompt):
    """
    Simple wrapper around LLM serving endpoint.
    For DBRX-style API that accepts 'input' or 'messages', adjust accordingly.
    """

    url = f"{DATABRICKS_HOST}{LLM_ENDPOINT}"

    payload = {
        "inputs": prompt
    }

    resp = requests.post(url, headers=HEADERS, data=json.dumps(payload))
    resp.raise_for_status()
    data = resp.json()

    # For many Databricks provided models, "predictions" is list of strings
    return data["predictions"][0]
```

> Note: The exact payload structure for LLM may differ based on the model (e.g., DBRX might require `messages`). Adjust based on your serving endpoint’s docs. For the lab, this generic form is enough to teach the pattern.

---

##  6. Core RAG Logic (Python Module)

Create `rag_core.py`:

```python
# rag_core.py
import os
import numpy as np

from dbx_client import call_embedding_endpoint

TOP_K = int(os.getenv("TOP_K", 3))

# Load chunks + embeddings into memory at process startup
CHUNKS_PATH = os.path.join("data", "chunks.npy")
EMB_PATH = os.path.join("data", "embeddings.npy")

chunks = np.load(CHUNKS_PATH, allow_pickle=True).tolist()
embeddings = np.load(EMB_PATH).astype("float32")   # shape: (N, D)


def retrieve_top_k(question: str, k: int = TOP_K):
    """
    Embed the question via Databricks, then compute cosine similarity against embeddings.
    Returns top-k (chunk, score) pairs.
    """
    # 1. Get question embedding from Databricks
    q_emb_list = call_embedding_endpoint([question])
    q_emb = np.array(q_emb_list[0], dtype="float32")

    # 2. Cosine similarity = (v · q) / (||v|| * ||q||)
    norms = np.linalg.norm(embeddings, axis=1) * np.linalg.norm(q_emb)
    sims = np.dot(embeddings, q_emb) / norms

    # 3. Get top-k indices
    top_idx = sims.argsort()[-k:][::-1]

    results = []
    for i in top_idx:
        results.append({
            "chunk": chunks[i],
            "score": float(sims[i])
        })

    return results


def build_rag_prompt(question: str, retrieved_chunks):
    """
    Build a RAG-style prompt with retrieved context.
    """
    context_text = "\n\n".join([c["chunk"] for c in retrieved_chunks])

    prompt = f"""
You are a helpful assistant. Use ONLY the context below to answer the question.

Context:
{context_text}

Question: {question}

If the answer is not in the context, say "I don't know based on the provided context."
"""

    return prompt
```

---

##  7. FastAPI Application

Create `app.py`:

```python
# app.py
from fastapi import FastAPI
from pydantic import BaseModel

from rag_core import retrieve_top_k, build_rag_prompt
from dbx_client import call_llm

app = FastAPI(
    title="RAG API",
    description="Production-style RAG API using Databricks Model Serving",
    version="1.0.0"
)


class RAGRequest(BaseModel):
    question: str
    top_k: int | None = None


class RAGResponse(BaseModel):
    answer: str
    question: str
    used_chunks: list[dict]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/rag/query", response_model=RAGResponse)
def rag_query(req: RAGRequest):
    # 1. Retrieve similar chunks
    k = req.top_k or 3
    retrieved = retrieve_top_k(req.question, k=k)

    # 2. Build prompt
    prompt = build_rag_prompt(req.question, retrieved)

    # 3. Call LLM via Databricks Serving
    answer = call_llm(prompt)

    # 4. Return structured response
    return RAGResponse(
        answer=answer,
        question=req.question,
        used_chunks=retrieved
    )
```

---

## ▶ 8. Run the RAG API

From your terminal (inside `rag_api/`):

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Expected log:

```text
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

##  9. Test the API

### Test health endpoint

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status": "ok"}
```

---

### Test RAG query

```bash
curl -X POST "http://localhost:8000/rag/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Delta Lake?",
    "top_k": 3
  }'
```

Sample response:

```json
{
  "answer": "Delta Lake is a storage layer that brings ACID transactions to big data workloads on the Lakehouse...",
  "question": "What is Delta Lake?",
  "used_chunks": [
    {
      "chunk": "Delta Lake ensures ACID transactions for big data workloads...",
      "score": 0.88
    },
    {
      "chunk": "Databricks Academy provides training on Lakehouse, ML, and AI...",
      "score": 0.63
    }
  ]
}
```

---
