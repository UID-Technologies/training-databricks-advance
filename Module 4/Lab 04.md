
# **Module 4 — Assembling a Complete RAG Application**

This module puts everything together:

- Chunking
- Embeddings
- Vector Index
- MLflow Tracking
- RAG Query Function
- Calling LLM for final answer

This is where learners build a **real working RAG system**.

#  **LAB 4 — End-to-End RAG App with MLflow**

### Learning Objectives
- Log an embedding model with MLflow
- Save chunked vector data
- Build a full RAG function
- Perform semantic retrieval
- Call LLM with context
- Produce grounded final answers


---

## **STEP 1 — Track Embedding Model with MLflow**

```python
import mlflow
import mlflow.pyfunc

class Embedder(mlflow.pyfunc.PythonModel):
    def load_context(self, context):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
    def predict(self, context, model_input):
        return self.model.encode(model_input).tolist()

mlflow.pyfunc.log_model(
    artifact_path="embedder",
    python_model=Embedder()
)
```



##  What this step does

###  Wraps the embedding model into an MLflow PyFunc model

* MLflow stores the model and environment
* Allows versioning
* Makes embedding reproducible
* Enables registration into MLflow Model Registry

###  `load_context()`

Loads the model when MLflow serves it.

###  `predict()`

Receives text → returns embeddings.

---

##  Why we do this

In production, we NEVER load models manually in every notebook.

We use MLflow because:

* Consistent versioning
* Audit trail
* Serving endpoints
* Easy deployment
* Reuse across RAG and Agent pipelines

---

##  Expected output

An MLflow run gets created:

```
Registered model at mlruns/.../embedder
```

You can also view it in **MLflow UI**.


---

## **STEP 2 — Create RAG Function**

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")

import numpy as np

def rag_query(question, vectors, chunks):
    # Embed question
    q_emb = model.encode(question)
    
    # Retrieve similar chunks
    sims = np.dot(vectors, q_emb)
    top = np.argsort(sims)[::-1][:3]
    context = "\n".join(chunks[i] for i in top)
    
    prompt = f"""
    Answer using ONLY the context below:

    {context}

    Question: {question}
    """

    return prompt
```

##  What this step does

This builds the **core RAG pipeline**:

### 1 **Embed the user question**

```
q_emb = model.encode(question)
```

### 2 **Compute similarity**

```
sims = np.dot(vectors, q_emb)
```

Here, higher dot-product = more similar.

### 3 **Retrieve top 3 chunks**

```
top = np.argsort(sims)[::-1][:3]
```

### 4 **Construct prompt**

```
Answer using ONLY the context below:
{context}
```

### 5 **Return full RAG prompt**

This prompt will be sent to DBRX or any LLM.

---

##  Why this step matters

This is the **heart of RAG**:

* Retrieves relevant knowledge
* Prevents hallucinations
* Grounds model answers
* Builds a structured prompt

This is EXACTLY how enterprise RAG systems work.

---

##  Expected output of `rag_query("What is Delta Lake?", index, chunks)`

A prompt that looks like:

```
Answer using ONLY the context below:

Delta Lake ensures ACID transactions...
MLflow manages experiments...
Databricks Academy provides training...

Question: What is Delta Lake?
```

This is the final prompt used by the LLM.

---


## **STEP 3 — Call LLM**

```python
response = llm.chat(rag_query("What is Delta Lake?", index, chunks))
print(response)
```



##  What this step does

###  Takes the prompt from the RAG function

###  Sends it to DBRX or the workspace’s default LLM

###  Returns a grounded, context-aware answer

Example result:

```
Delta Lake is a storage layer that provides ACID transactions 
for big data workloads, enabling reliability on the Lakehouse.
```

---

##  Why this step is important

This is the **final stage** of the pipeline:

* Retrieval
* Augmentation
* LLM inference
* Summarization / QA

You now have a **complete end-to-end RAG application**.

---

#  **End-to-End RAG Flow Summary**

This lab builds the production flow:

```
PDF → Extract Text → Chunk → Embedding → Vector Index → RAG Prompt → LLM Answer
```

Databricks components involved:

| Stage         | Component                    |
| ------------- | ---------------------------- |
| Extraction    | Notebooks / PyMuPDF          |
| Chunking      | Python                       |
| Embeddings    | SentenceTransformer / MLflow |
| Storage       | Delta Lake                   |
| Vector Search | FAISS or Mosaic AI           |
| Reasoning     | RAG Function                 |
| Generation    | DBRX / LLM                   |
| Tracking      | MLflow                       |

This is the **entire architecture** behind production-grade RAG and agent systems.

---

