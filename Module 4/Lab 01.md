
# **Module 1 — Introduction to RAG**

##  What is RAG?

Retrieval-Augmented Generation (RAG) is an architecture where:

**LLM Response = LLM + retrieved relevant context**

Instead of depending only on the model’s internal knowledge, RAG retrieves **documents from your dataset**, feeds them to the LLM, and produces **accurate, grounded answers**.

### Core Components:

* **Document Storage** (Delta tables / Volumes)
* **Chunks** (small text pieces)
* **Embeddings** (vector representation)
* **Vector Store** (FAISS / Mosaic AI Vector Search)
* **Retriever**
* **LLM** (OpenAI/DBRX/MPT/Llama)
* **RAG Pipeline** (Databricks notebooks + MLflow)

---

# **LAB 1 — Introduction to RAG**

###  Learning Objectives

* Understand RAG flow end-to-end
* Load sample documents
* Create simple chunks
* Generate embeddings
* Retrieve relevant text manually
* Feed retrieved context into an LLM

---

## **STEP 0 — Create Notebook**

Notebook name:
**01_RAG_Introduction**

---

## **STEP 1 — Load Sample Documents**

Upload a simple text file (FAQ / knowledge base) into DBFS.

```python

# -----------------------------------------------------------
# STEP 1 — Load Sample Text File
# -----------------------------------------------------------

path = "/Volumes/workspace/rag/raw/sample_docs.txt"



dbutils.fs.put(path, """
Databricks Academy provides training on Lakehouse, ML, and AI.
Delta Lake ensures ACID transactions for big data workloads.
Vector search enables efficient similarity search across embeddings.
MLflow manages experiments, models, and deployment pipelines.
""", True)
```

###  What this step does

1. **Defines a file path** inside a Volume (`/Volumes/...`)

   * Volumes are Unity Catalog–governed storage locations.
2. **Creates a raw sample text file** using `dbutils.fs.put()`.
3. **Writes multiple lines** of text that will be used for RAG.

###  Why this step is needed

RAG needs **documents**.
This step creates a **dummy knowledge base** to simulate enterprise data.

---

## **STEP 2 — Read Documents**

```python

# -----------------------------------------------------------
# STEP 2 — Read Document
# -----------------------------------------------------------


df_raw = spark.read.text(path)
df_raw.show(truncate=False)

rows = spark.read.text(path).collect()
text = "\n".join([r["value"] for r in rows if r["value"].strip() != ""])

display(text)
```

### What this step does

1. Reads the text file into a Spark DataFrame.
2. Shows each line as a separate row.

### Why this is needed

To confirm the file exists and the content loaded correctly.

### Expected output

A table like:

| value                        |
| ---------------------------- |
| Databricks Academy provides… |
| Delta Lake ensures…          |
| Vector search enables…       |
| MLflow manages…              |
| RAG combines…                |
---

## **STEP 3 — Chunk the Document**

```python

# -----------------------------------------------------------
# STEP 3 — Simple Chunking
# -----------------------------------------------------------

import textwrap

chunks = textwrap.wrap(text, width=80)
chunks
```


### What this does

Splits the text into smaller pieces ("chunks") of about **80 characters each**.

### Why this is needed

LLMs work best when fed **small, semantically meaningful pieces**.

Chunking is KEY to RAG because:

* Prevents using entire documents
* Reduces cost
* Improves accuracy
* Improves retrieval

### Expected output

A list of 2–4 chunks, like:

```
[
 "Databricks Academy provides training...",
 "Delta Lake ensures ACID...",
 "Vector search enables...",
 ...
]
```



---

## **STEP 4 — Generate Embeddings (OpenAI / HuggingFace)**

Using HuggingFace:

```python

# -----------------------------------------------------------
# STEP 4 — Embeddings (HuggingFace)
# -----------------------------------------------------------

from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(chunks, convert_to_tensor=False)
```



### What this does

1. Loads the **MiniLM embedding model**
2. Converts each chunk into a **numerical vector** representation

### Why this is needed

Embeddings allow us to measure **semantic similarity**.
This lets the system find relevant chunks for user queries.

### Expected output

`embeddings` becomes a list like:

```
[
 [0.12, -0.44, 0.75, ... 384 dims],
 [0.98,  0.11, -0.09, ...],
 ...
]
```

---

## **STEP 5 — Store Chunks in a Delta Table**

```python

# -----------------------------------------------------------
# STEP 5 — Save as Delta Table
# -----------------------------------------------------------

import pandas as pd

df = pd.DataFrame({"chunk": chunks, "embedding": embeddings.tolist()})
spark_df = spark.createDataFrame(df)

spark_df.write.format("delta").mode("overwrite").save("/FileStore/rag/chunks_delta")
```




### What this does

1. Creates a Spark DataFrame containing **chunks + embeddings**
2. Writes it as a **Delta table** inside a governed volume

### Why this is needed

A RAG system must:

* Persist chunked knowledge
* Enable fast retrieval later
* Keep embeddings reusable across notebooks

### Expected output

No visual output → silent write (correct)

Verify with:

```python
spark.read.format("delta").load("/Volumes/.../chunks_delta").show()
```



---

## **STEP 6 — Retrieve Similar Text**

```python
# -----------------------------------------------------------
# STEP 6 — Retrieve Similar Chunk
# -----------------------------------------------------------

import numpy as np

query = "What is Delta Lake?"
query_emb = model.encode([query])[0]

spark_df = spark.read.format("delta").load("/FileStore/rag/chunks_delta")
local_df = spark_df.toPandas()

local_df["similarity"] = local_df["embedding"].apply(
    lambda x: np.dot(x, query_emb)
)

local_df.sort_values("similarity", ascending=False).head(3)
```



### What this does

1. Encodes the query into an embedding
2. Computes **dot-product similarity**
3. Finds the **most relevant chunks**

### Why this is needed

This is the **retriever** in RAG:

* Finds relevant context
* Helps LLM answer correctly
* Prevents hallucinations

### Expected output

A table like:

| chunk                        | embedding | similarity |
| ---------------------------- | --------- | ---------- |
| Delta Lake ensures ACID…     | […]       | **0.85**   |
| Databricks Academy provides… | […]       | 0.42       |

Top row = most relevant chunk.



---

## **STEP 7 — Ask LLM Using Retrieved Context**

(Trial workspace example with DBRX or OpenAI if allowed)

```python

# -----------------------------------------------------------
# STEP 7 — Ask LLM using Retrieved Context
# -----------------------------------------------------------

context = local_df.sort_values("similarity", ascending=False).head(2)["chunk"].str.cat("\n")

prompt = f"""
Use ONLY the following context to answer:

{context}

Question: {query}
"""

print(prompt)
```

If DBRX available:

```python
from databricks import llm

llm.chat(prompt)
```




### What this does

1. Selects **top 2 most similar chunks**
2. Builds a RAG-style prompt
3. Shows the final prompt sent to an LLM

### Why this is needed

This is the **generation phase** of RAG:

* LLM receives context
* LLM answers grounded on real company documents

### Expected output

A prompt like:

```
Use ONLY this context to answer:

Databricks Academy provides training on Lakehouse, ML, and AI.
Delta Lake ensures ACID transactions for big data workloads.

Question: What is Databricks?
```

If you now call:

```python
from databricks import llm
llm.chat(prompt)
```

Expected answer:

```
Databricks is a unified data and AI platform that provides training on Lakehouse, ML, and AI.
```


---




# Trouble Shooting

###  **Fix: Install `sentence-transformers` in Databricks notebook**

Add this **as the first cell** in your notebook:

```python
%pip install sentence-transformers
dbutils.library.restartPython()
```

### Why restart?

Because Databricks requires a Python restart after installing new libraries.

---

### Important Notes for Databricks Trial Edition

#### `%pip install` **works**

This installs into notebook-scoped Python environment.

#### After restarting Python

You MUST rerun all cells in the notebook again (imports, variables, chunk logic, etc.).

---

### **Full Working Setup Cell (Recommended)**

Paste this at the top of your notebook:

```python
# Install HF embeddings model + dependencies
%pip install sentence-transformers==2.2.2
%pip install accelerate

# Restart Python to activate libraries
dbutils.library.restartPython()
```
