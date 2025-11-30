# **LAB 3 — Automated RAG Evaluation Pipeline**

## *(Automated RAG → Metrics → Delta → Dashboard Refresh)*

This lab teaches how to automate evaluation workflows using **Databricks Workflows (Jobs)**—a key skill for RAG/LLM production systems.

---

#  **Learning Objectives**

Learners will:

- Build a Databricks **Workflow Job**
- Automate RAG evaluation over multiple questions
- Store RAG metrics into **Delta Lake**
- Compute BLEU / ROUGE / LLM-as-a-Judge automatically
- Chain notebooks using **dependencies**
- Add **alerts**, **retries**, **schedules**, **auto-refresh dashboards**
- Build CI/CD-like evaluation loop for RAG

After this lab, your RAG system becomes **self-evaluating**.

---

#  **End-to-End Architecture**

```
   ┌────────────────┐
   │ Notebook 1     │
   │ load_eval_qs   │  -> Load test questions
   └────────────────┘
            ↓
   ┌────────────────┐
   │ Notebook 2     │
   │ run_rag_eval   │  -> Generate answers using RAG
   └────────────────┘
            ↓
   ┌────────────────┐
   │ Notebook 3     │
   │  eval_metrics  │  -> BLEU / ROUGE / Judge
   └────────────────┘
            ↓
   ┌──────────────────────────────────┐
   │ Delta Table: rag_secure.eval_gold │
   └──────────────────────────────────┘
            ↓
   ┌──────────────────────┐
   │ Dashboard Refresh     │
   └──────────────────────┘
```

This workflow mimics **real enterprise MLOps / LLMOps pipelines**.

---



#  **STEP 1 — Notebook 1 (load_eval_qs)**



###  Purpose

This notebook loads the list of **test questions** used for evaluation.

---

###  Create Notebook: `load_eval_qs`

```python
import pandas as pd

# Evaluation questions (expand anytime)
questions = [
    "What is Delta Lake?",
    "Explain ACID transactions.",
    "What is Unity Catalog?",
    "What is MLflow?",
    "Explain Vector Search."
]

pdf = pd.DataFrame({"question": questions})

df = spark.createDataFrame(pdf)

df.write.format("delta").mode("overwrite") \
    .saveAsTable("rag_secure.eval_questions")

display(df)
```

### ✔ Expected Output

A Delta table:

```
rag_secure.eval_questions
```

containing 5–10 test queries.

---


#  **STEP 2 — Notebook 2 (run_rag_eval)**


###  Purpose

Runs your **RAG pipeline** on each question and stores answers.

---

###  Create Notebook: `run_rag_eval`

```python
import pandas as pd
import numpy as np
from databricks import llm

# Load questions
df_q = spark.read.table("rag_secure.eval_questions")
questions = [r["question"] for r in df_q.collect()]

# Load vector store (from earlier labs)
df_chunks = spark.read.load("/Volumes/workspace/lab/myvolume/prepared_chunks")
local_df = df_chunks.toPandas()

chunks = local_df["chunk"].tolist()
vectors = np.array(local_df["embedding"].tolist()).astype("float32")

# Load embedding model
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")

def rag_query(question):
    q_emb = model.encode(question)
    sims = np.dot(vectors, q_emb)
    top_idx = np.argsort(sims)[::-1][:3]
    
    context = "\n".join([chunks[i] for i in top_idx])
    
    return f"""
Use ONLY the context below:

{context}

Question: {question}
"""

results = []
for q in questions:
    prompt = rag_query(q)
    answer = llm.chat(prompt)
    results.append((q, answer))

df_rag = pd.DataFrame(results, columns=["question", "generated"])

spark.createDataFrame(df_rag).write.format("delta").mode("overwrite") \
    .saveAsTable("rag_secure.eval_answers")
```

---


#  **STEP 3 — Notebook 3 (eval_metrics)**


###  Purpose

Compute **BLEU, ROUGE, LLM-as-a-Judge, avg_score**, and append to GOLD table.

---

###  Create Notebook: `eval_metrics`

```python
from sacrebleu import corpus_bleu
from rouge_score import rouge_scorer
from databricks import llm
import pandas as pd
import json

df_ans = spark.read.table("rag_secure.eval_answers")
rows = df_ans.toPandas()

gold = []

for row in rows.itertuples():
    q = row.question
    gen = row.generated

    # Replace with your real reference answers!
    reference = "This is a placeholder reference. Replace with gold truths."

    # BLEU
    bleu = corpus_bleu([gen], [[reference]]).score

    # ROUGE
    scorer = rouge_scorer.RougeScorer(["rouge1", "rougeL"])
    rouge = scorer.score(reference, gen)

    # LLM-as-a-Judge
    judge_prompt = f"""
Rate the answer 1–5 (correctness, groundedness, safety).
Return JSON: {{"correctness":X,"groundedness":Y,"safety":Z}}

Question: {q}
Answer: {gen}
"""
    judge_raw = llm.chat(judge_prompt)
    judge = json.loads(judge_raw)

    gold.append({
        "question": q,
        "generated": gen,
        "bleu": bleu,
        "rouge1": rouge["rouge1"].fmeasure,
        "rougeL": rouge["rougeL"].fmeasure,
        "correctness": judge["correctness"],
        "groundedness": judge["groundedness"],
        "safety": judge["safety"],
        "avg_score": (judge["correctness"] + judge["groundedness"] + judge["safety"]) / 3
    })

df_gold = spark.createDataFrame(pd.DataFrame(gold))

df_gold.write.format("delta").mode("append") \
    .saveAsTable("rag_secure.eval_results_gold")
```

---


#  **STEP 4 — Create Databricks Job (NEW UI)**


###  Navigation

**Workflows → Jobs → Create Job**

---

## Task 1 — `load_eval_qs`

* Type: Notebook
* Path: your `load_eval_qs` notebook
* Compute: all-purpose cluster

---

##  Task 2 — `run_rag_eval`

* Depends on: `load_eval_qs`
* Notebook: `/run_rag_eval`

---

##  Task 3 — `eval_metrics`

* Depends on: `run_rag_eval`
* Notebook: `/eval_metrics`

---



#  **STEP 5 — Add Schedules, Alerts, Retries**

-

###  Add Schedule

* Enable schedule
* Run: **Daily at 09:00 AM**

---

###  Add Retry Logic

Task → Advanced Settings:

```
Retries: 3
Retry interval: 120 seconds
```

---

###  Add Email Alert

Workflow → Alerts:

```
On Failure → Email → your_team@company.com
```

Works exactly like production pipelines.

---


#  **STEP 6 — Validate the Pipeline**


Run:

```sql
SELECT *
FROM rag_secure.eval_results_gold
ORDER BY avg_score DESC;
```

You should see:

| question | bleu | rouge | correctness | groundedness | safety | avg_score |
| -------- | ---- | ----- | ----------- | ------------ | ------ | --------- |

Each Job run adds new evaluation rows.

---


#  **STEP 7 — Dashboard Auto-Refresh**


From Previous Lab Dashboard:

1. Open Dashboard
2. Click **Edit Dashboard**
3. Enable **Auto-refresh every 5 minutes**
4. Data source = `rag_secure.eval_results_gold`

Your dashboard now tracks model performance **continuously**.

---

#  **LAB Completed!**

You built:

- Automated RAG evaluation pipeline
- Multi-step job orchestration
- BLEU/ROUGE/Judge metrics
- GOLD evaluation dataset
- Scheduled evaluation
- Alerts + retry logic
- Auto-refreshing dashboards

This is exactly how Databricks customers monitor RAG/LLM apps in production.

---
