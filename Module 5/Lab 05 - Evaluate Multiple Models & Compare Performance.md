
#  **LAB 5 — Evaluate Multiple Models & Compare Performance**

### *(DBRX vs LLama 3 vs External Models — Enterprise Model Bake-Off)*

---

#  **Learning Objectives**

By the end of this lab, learners will:

✔ Evaluate a **single RAG pipeline** across multiple LLM models
✔ Measure **accuracy, groundedness, safety, latency**
✔ Compute **BLEU**, **ROUGE**, and **LLM-as-a-Judge** metrics
✔ Store evaluation results in **Delta Lake**
✔ Build a **Model Comparison Dashboard**
✔ Select the best model for a **production RAG workload**

This lab mirrors real enterprise **model bake-off** processes used in:

* Banking
* Insurance
* Healthcare
* Pharma
* Manufacturing
* Large B2C support systems

---

#  **Architecture: Multi-Model Evaluation Pipeline**

```
                 ┌────────────────────────┐
                 │   Evaluation Questions │
                 └────────────────────────┘
                            ↓
           ┌───────────────────────────────────────┐
           │     Shared RAG Prompt (Grounded)       │
           └───────────────────────────────────────┘
            ↓                ↓                 ↓
   ┌───────────────┐ ┌───────────────┐ ┌─────────────────┐
   │   DBRX         │ │   Llama 3     │ │ External Model  │
   └───────────────┘ └───────────────┘ └─────────────────┘
            ↓                ↓                 ↓
   ┌────────────────────────────────────────────────────┐
   │ BLEU | ROUGE | LLM Judge | Latency | Avg Score     │
   └────────────────────────────────────────────────────┘
                            ↓
           ┌────────────────────────────────────┐
           │ Delta Table: model_eval_comparison │
           └────────────────────────────────────┘
                            ↓
           ┌──────────────────────────┐
           │   Comparison Dashboard   │
           └──────────────────────────┘
```

---


#  **STEP 0 — Notebook Setup**


Create notebook:

```
09_model_comparison
```

Install dependencies:

```python
%pip install sacrebleu rouge-score
dbutils.library.restartPython()
```

Imports:

```python
import time
import json
import numpy as np
import pandas as pd

from databricks import llm
from sacrebleu import corpus_bleu
from rouge_score import rouge_scorer
```

Load test questions (from LAB 5 pipeline):

```python
df_q = spark.read.table("rag_secure.eval_questions")
questions = [r["question"] for r in df_q.collect()]
```

Load vector DB (RAG chunks):

```python
df_chunks = spark.read.load("/Volumes/workspace/lab/myvolume/prepared_chunks")
local_df = df_chunks.toPandas()

chunks = local_df["chunk"].tolist()
vectors = np.array(local_df["embedding"].tolist()).astype("float32")
```

Load embedding:

```python
from sentence_transformers import SentenceTransformer
embedder = SentenceTransformer("all-MiniLM-L6-v2")
```

---


#  **STEP 1 — Create Shared RAG Prompt for All Models**


This ensures no model has an advantage.

```python
def build_rag_prompt(question):
    q_emb = embedder.encode(question)
    sims = np.dot(vectors, q_emb)
    top = np.argsort(sims)[::-1][:3]

    context = "\n".join([chunks[i] for i in top])

    return f"""
You must answer using ONLY the provided context.
If the answer cannot be found, respond: "I don't know."

Context:
{context}

Question: {question}
"""
```

---


#  **STEP 2 — Create Model Adapters**


## **2.1 DBRX**

```python
def call_dbrx(prompt):
    start = time.time()
    ans = llm.chat(prompt)
    return ans, time.time() - start
```

---

## **2.2 Llama 3**

```python
def call_llama(prompt):
    start = time.time()
    ans = llm.chat(prompt, model="llama3")
    return ans, time.time() - start
```

---

## **2.3 External Model Adapter (Optional)**

```python
import requests

def call_external(prompt):
    start = time.time()
    resp = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer <API_KEY>"},
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt}]
        }
    ).json()
    answer = resp["choices"][0]["message"]["content"]
    return answer, time.time() - start
```

---


#  **STEP 3 — Define Evaluation Metrics**


BLEU + ROUGE:

```python
scorer = rouge_scorer.RougeScorer(["rouge1", "rougeL"])

def compute_scores(reference, generated):
    bleu = corpus_bleu([generated], [[reference]]).score
    rouge_vals = scorer.score(reference, generated)

    return {
        "bleu": bleu,
        "rouge1": rouge_vals["rouge1"].fmeasure,
        "rougeL": rouge_vals["rougeL"].fmeasure
    }
```

---

LLM-as-a-Judge:

```python
judge_template = """
Rate correctness, groundedness and safety on a scale of 1 to 5.
Return JSON only: {"correctness":X, "groundedness":Y, "safety":Z}

Question: {q}
Answer: {a}
"""

def llm_judge(q, a):
    out = llm.chat(judge_template.format(q=q, a=a))
    return json.loads(out)
```

---


#  **STEP 4 — Run Evaluation Across All Models**


Reference answers (trainer-editable):

```python
reference_answers = {
    "What is Delta Lake?": "Delta Lake brings ACID transactions to the Lakehouse.",
    "Explain ACID transactions.": "ACID stands for Atomicity, Consistency, Isolation, Durability.",
    "What is Unity Catalog?": "Unity Catalog is a unified governance layer for Databricks.",
    "What is MLflow?": "MLflow manages ML lifecycle: tracking, models, registry.",
    "Explain Vector Search.": "Vector Search retrieves semantically similar embeddings."
}
```

Run evaluation:

```python
results = []

models = {
    "dbrx": call_dbrx,
    "llama3": call_llama,
    # "external": call_external
}

for q in questions:
    prompt = build_rag_prompt(q)
    reference = reference_answers.get(q, "")

    for model_name, fn in models.items():
        response, latency = fn(prompt)

        metric = compute_scores(reference, response)
        judge = llm_judge(q, response)

        row = {
            "question": q,
            "model": model_name,
            "response": response,
            "latency_sec": latency,
            "bleu": metric["bleu"],
            "rouge1": metric["rouge1"],
            "rougeL": metric["rougeL"],
            "correctness": judge["correctness"],
            "groundedness": judge["groundedness"],
            "safety": judge["safety"],
            "avg_score": (
                judge["correctness"] +
                judge["groundedness"] +
                judge["safety"]
            ) / 3
        }

        results.append(row)
```

---

#  **STEP 5 — Save Evaluation Results to Delta**


```python
df_results = spark.createDataFrame(pd.DataFrame(results))

df_results.write.format("delta").mode("append") \
    .saveAsTable("rag_secure.model_eval_comparison")
```

---


#  **STEP 6 — Build Model Comparison Dashboard**


Go to:

**SQL → Dashboards → Create Dashboard**

Name it:

```
Model Comparison — RAG Evaluation
```

Add visuals:

---

###  1. BLEU Score Comparison

```sql
SELECT model, AVG(bleu) AS avg_bleu
FROM rag_secure.model_eval_comparison
GROUP BY model;
```

---

###  2. ROUGE-L Comparison

```sql
SELECT model, AVG(rougeL) AS avg_rougeL
FROM rag_secure.model_eval_comparison
GROUP BY model;
```

---

###  3. LLM Judge Metrics (Correctness, Groundedness, Safety)

```sql
SELECT model,
       AVG(correctness) AS correctness,
       AVG(groundedness) AS groundedness,
       AVG(safety) AS safety
FROM rag_secure.model_eval_comparison
GROUP BY model;
```

---

###  4. Latency Comparison

```sql
SELECT model, AVG(latency_sec)
FROM rag_secure.model_eval_comparison
GROUP BY model;
```

---

###  5. Final Model Quality Score

```sql
SELECT model, AVG(avg_score) AS model_quality
FROM rag_secure.model_eval_comparison
GROUP BY model;
```

---



#  **STEP 7 — Identify Best Model Automatically**


```sql
SELECT model, AVG(avg_score) AS score
FROM rag_secure.model_eval_comparison
GROUP BY model
ORDER BY score DESC;
```

---

#  **Lab — COMPLETE**

You have now built a:

✔ Multi-model evaluation system
✔ RAG-grounded comparison pipeline
✔ BLEU/ROUGE + LLM-Judge scoring system
✔ Latency-based model ranking
✔ Delta-based evaluation store
✔ Full dashboard for model selection

This is **exactly what enterprise AI/ML teams use** in real-world LLM platform evaluations.

---
