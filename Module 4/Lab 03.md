# **Module 3 — Mosaic AI Vector Search**

This module introduces learners to **semantic vector search**, a core part of RAG systems.

Vector search allows us to find chunks that are **semantically similar** to a user query — not just keyword matches.

---

# **What is a Vector Store?**

A vector store is a database specialized for **embedding vectors**.

Each record contains:

| Field         | Purpose                              |
| ------------- | ------------------------------------ |
| **ID**        | Unique chunk ID                      |
| **Chunk**     | The text that was embedded           |
| **Embedding** | Numerical vector representation      |
| **Metadata**  | Source file, page number, tags, etc. |

### Why vector stores are needed

Traditional search (SQL / keyword) fails to match:

* Similar meaning
* Paraphrases
* Synonyms
* Conceptual matches

Vector search solves this with **semantic similarity**.

---

# Vector Store Options in Databricks

| Option                      | Availability     | Notes                                      |
| --------------------------- | ---------------- | ------------------------------------------ |
| **Mosaic AI Vector Search** | Enterprise / Pro | Fully managed, scalable index              |
| **FAISS**                   | Always available | Local vector search (CPU), ideal for Trial |

FAISS = Facebook AI Similarity Search — an industry standard.

---

#  **LAB 3 — Vector Search with Databricks**

###  Learning Objectives

By completing this lab, learners will:

✔ Understand vector indexes
✔ Insert embeddings into a vector index
✔ Query based on semantic similarity
✔ Filter top-K relevant chunks

They will also understand how RAG retrieves context.


---

## **STEP 0 — Pre Setup**
```python

%pip install sentence-transformers
%pip install accelerate
%pip install faiss-cpu
dbutils.library.restartPython()

import numpy as np

df = spark.read.format("delta").load("/Volumes/workspace/lab/myvolume/prepared_chunks")
local_df = df.toPandas()

chunks = local_df["chunk"].tolist()
vectors = np.array(local_df["embedding"].tolist()).astype("float32")

```


## **STEP 1 — Create Vector Search Collection**

### Option A — Mosaic Vector Search (Only if enabled)

```python
from databricks.vectorsearch.client import VectorSearchClient

client = VectorSearchClient()

client.create_collection(
    name="rag_vectors",
    catalog="rag_catalog",
    schema="vectors",
    primary_key="id",
    embedding_dimension=384
)
```

### What this does

* Creates a **managed vector index** in Unity Catalog
* Embeddings are stored efficiently
* Supports real-time search
* Auto-managed scaling, sharding, partitioning

### Expected result

A vector search collection like:

```
rag_catalog.vectors.rag_vectors
```

### Option B — FAISS (Guaranteed to work in Trial)

```python
import faiss
import numpy as np


dim = vectors.shape[1]
index = faiss.IndexFlatL2(dim)
index.add(vectors)
```



### What this does

* Uses **FAISS L2 distance index**
* Converts embeddings into a NumPy matrix
* Adds all vectors into the index

### Why FAISS works well in Databricks

* No dependencies beyond NumPy
* Very fast
* Works fully locally
* Good for teaching concepts

### Expected output

Nothing (FAISS `.add()` is silent)

Check count:

```python
index.ntotal
```

Output:

```
5
```

(or however many chunks you have)




---

## **STEP 2 — Query Vector Search**

```python
query = "Explain Databricks training"
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")

q_emb = model.encode(query).astype("float32")

D, I = index.search(np.array([q_emb]), k=3)
I[0]
```



###  What this does

1. Converts the **query text** into an embedding (`q_emb`)
2. Searches FAISS index for **top-3 closest embeddings**
3. Returns:

   * **D** = distances (lower is better)
   * **I** = indices of matched vectors

### Example output

```
array([2, 0, 1])
```

Meaning the top semantic match was chunk index **2** in the original `chunks` list.

### Why this matters

This is the heart of retrieval in a RAG system.


---

## **STEP 3 — Filter Highly Relevant Chunks**

Filter by cosine similarity > 0.5

```python
threshold = 0.50
results = []

for v, chunk in zip(vectors, chunks):
    sim = float(np.dot(v, q_emb) / (np.linalg.norm(v) * np.linalg.norm(q_emb)))
    if sim > threshold:
        results.append((chunk, sim))

sorted(results, key=lambda x: x[1], reverse=True)[:5]
```


###  What this does

This step computes **cosine similarity** between:

* query embedding
* each chunk embedding

Then filters based on threshold `0.5`.

### Give this explanation:

> “L2 distance gives nearest neighbors but cosine similarity gives *semantic match quality*.”

### Expected output example

```
[
  ("Databricks Academy provides training on Lakehouse, ML, and AI.", 0.78),
  ("MLflow manages experiments, models, and pipelines.", 0.66)
]
```

These are the **most relevant chunks** for the query:

> "Explain Databricks training options."



```

0.75 - 0.90 - very good match
0.55 - 0.70 - relavent
0.30 - 0.50 - weak
0.05 - 0.20 - random
```

---

