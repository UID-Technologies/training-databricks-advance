# **Module 2 — Preparing Data for RAG Solutions**

## **2.1 Data Storage & Governance**

You will use:

* **Delta Tables**
* **Unity Catalog (optional if trial supports UC)**
* **DBFS or Volumes**

---

#  **LAB 2 — Preparing Data for RAG**

###  Learning Objectives

* Store raw documents
* Apply chunking
* Build embeddings
* Save clean vector-ready dataset

---

## **STEP 1 — Create Catalog & Schema (if UC enabled)**

```sql
CREATE CATALOG IF NOT EXISTS rag_catalog;
CREATE SCHEMA IF NOT EXISTS rag_catalog.raw;
CREATE SCHEMA IF NOT EXISTS rag_catalog.prepared;
```

### What this does

* Creates a **governed home** for your RAG data.
* Organizes it into:

  * `raw` → Raw PDF/TXT/CSV ingested
  * `prepared` → Clean chunks + embeddings

### Why this matters

RAG pipelines need structured medallion architecture:

| Layer  | Store                               |
| ------ | ----------------------------------- |
| Bronze | Raw documents                       |
| Silver | Clean chunks & embeddings           |
| Gold   | Aggregations, vector search indexes |

This step sets up the **Silver zone** for your RAG project.

### Expected output

```
Catalog created.
Schema created.
```

If UC is NOT enabled → skip this step and use DBFS only.


---

## **STEP 2 — Upload PDFs / Text Files**

Use "Upload to DBFS".

Target folder:

```
/Volumes/workspace/rag/raw/
```




### Why this matters

RAG can't ingest PDFs directly — they must be placed in a folder
where your Spark cluster can read and process them.

### Expected output for checking files:

```python
display(dbutils.fs.ls("/Volumes/workspace/rag/raw/"))
```

Output sample:

| name        | size  |
| ----------- | ----- |
| sample1.pdf | 18 KB |


---

## **STEP 3 — Extract Text from Files**

```python
import fitz  # PyMuPDF

pdf_path = "/Volumes/workspace/rag/raw/sample1.pdf"
doc = fitz.open(pdf_path)

text = ""
for page in doc:
    text += page.get_text()

print(text[:500])
```



###  What this does

* Opens the PDF
* Reads each page
* Extracts text using PyMuPDF
* Combines into a single text string

###  Why this matters

RAG needs **clean text**, not PDFs.

LLMs and vector models cannot “read” PDFs unless text is extracted.

###  Expected output

First 500 chars of the PDF content.

If the output is blank:

❗ Your PDF is an image → requires OCR (Tesseract / Azure Document Intelligence)


---

## **STEP 4 — Chunking the Content**

Chunk into 200–300 token blocks.

```python
def chunk_text(text, max_len=300):
    sentences = text.split(". ")
    chunks = []
    current = ""

    for s in sentences:
        if len(current) + len(s) < max_len:
            current += s + ". "
        else:
            chunks.append(current)
            current = s + ". "
    chunks.append(current)
    return chunks

chunks = chunk_text(text)
len(chunks)
```


###  What this does

Splits the PDF text into smaller, manageable “chunks” (~300 characters).

### Why chunking is required:

* LLM context limits
* Better similarity search
* More precise retrieval
* Lower latency
* Lower cost
* Prevents passing full documents to LLM

### Expected output

A number:

```
5
```

(or more depending on PDF length)

### Optional:

Show chunk preview:

```python
chunks[0]
```


---

## **STEP 5 — Generate Embeddings**

```python
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")

vector_data = [(c, model.encode(c).tolist()) for c in chunks]
```



###  What this does

Creates a list of:

```
(chunk_text, embedding_vector)
```

Example:

```
("Databricks helps organizations...", [0.12, -0.55, 0.77, ...])
```

### Why embeddings matter

They allow RAG to:

* Perform semantic search
* Match queries to relevant chunks
* Build context for LLM prompts

### Expected output

`vector_data` list of tuples.




---

## **STEP 6 — Save Prepared Data**

```python
df = spark.createDataFrame(vector_data, ["chunk", "embedding"])
df.write.format("delta").mode("overwrite").saveAsTable("rag_catalog.prepared.chunks")
```


###  What this does

* Converts chunks & embeddings into a Spark DataFrame
* Saves it as a **Delta table** under:

```
rag_catalog.prepared.chunks
```

### Why this matters

You now have a **vector-ready dataset**.

This table is used in:

* LAB 3 — Vector Search
* LAB 4 — RAG Pipeline
* LAB 5 — MLflow / Orchestration

### Expected output

Check with:

```python
SELECT * FROM rag_catalog.prepared.chunks LIMIT 5;
```

Example output:

| chunk                 | embedding            |
| --------------------- | -------------------- |
| "Databricks helps..." | `[0.12, -0.55, ...]` |

---



# **Trouble Shooting**

You're getting:

```
ModuleNotFoundError: No module named 'fitz'
```

This means **PyMuPDF is not installed** in your Databricks notebook environment.

But Databricks Trial Edition *does allow* `%pip install`, so the fix is simple.

---

### **Fix: Install PyMuPDF (fitz)**

Run this cell at the TOP of your notebook:

```python
%pip install sentence-transformers
%pip install accelerate
dbutils.library.restartPython()
```

After restart, re-run all previous cells.

---
