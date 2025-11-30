
# 🧪 **LAB 02 — Build a Complete RAG Evaluation Dashboard in Databricks**

### *(BLEU, ROUGE, LLM-as-a-Judge, Groundedness, Safety, UC Tables, Dashboards)*

---

#  **Lab Goals**

By the end of this standalone lab, a learner will:

✔ Compute BLEU & ROUGE evaluation metrics
✔ Evaluate correctness, groundedness, safety using an LLM
✔ Store results in a Delta table
✔ Build an analytics **Gold evaluation table**
✔ Create a Databricks **Interactive Dashboard**
✔ Identify hallucinations & unsafe responses
✔ Build an enterprise-grade evaluation workflow for RAG/LLM systems

---

#  **Prerequisites (Minimal)**

Nothing from other labs is required.

Only ensure:

### 1 A Databricks workspace

### 2 A user cluster or SQL warehouse

### 3 **One LLM Chat endpoint** (function calling not required)

Use any supported Databricks Foundation Model endpoint
(examples in your workspace: Llama 3.1 70B, Qwen, GPT-5.1, etc.)

In this lab we use:

```
databricks-meta-llama-3-1-405b-instruct
```

Replace with any chat endpoint you prefer.

---



#  **STEP 0 — Setup: Import Libraries + Configure LLM Endpoint**



This block sets up everything:

* Imports BLEU, ROUGE libraries
* Connects to your Databricks LLM endpoint
* Creates a helper function `llm_chat()`

 **Self-contained — nothing external required.**

---

```python
# COMMAND ----------

# Install eval libraries if missing
%pip install sacrebleu rouge-score --quiet

import json
import requests
import pandas as pd
from sacrebleu import corpus_bleu
from rouge_score import rouge_scorer

# ------------------------------
# Databricks Workspace + Token
# ------------------------------
workspace = spark.conf.get("spark.databricks.workspaceUrl")
token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

# ------------------------------
# LLM Endpoint (Chat Model)
# ------------------------------
LLM_ENDPOINT = "databricks-meta-llama-3-1-405b-instruct"
LLM_URL = f"https://{workspace}/serving-endpoints/{LLM_ENDPOINT}/invocations"

HEADERS = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

def llm_chat(prompt: str) -> str:
    """Send a prompt to the LLM and return assistant text."""
    payload = {"messages": [{"role": "user", "content": prompt}]}
    resp = requests.post(LLM_URL, headers=HEADERS, data=json.dumps(payload))
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]
```

---



#  **STEP 1 — Create Sample Evaluation Example**



This lab generates **one evaluation row**, but you can loop it for many questions.

We evaluate:

* BLEU
* ROUGE-1 & ROUGE-L
* correctness (1–5)
* groundedness (1–5)
* safety (1–5)

This is **fully standalone** — we provide question, reference, and generated answer.

---

```python
# COMMAND ----------

# Sample data for evaluation
question = "What is Delta Lake?"
reference = "Delta Lake is a reliable storage layer that brings ACID transactions to data lakes."
generated = "Delta Lake manages ACID transactions and ensures reliability for big data."

# -------------------
# BLEU
# -------------------
bleu = corpus_bleu([generated], [[reference]]).score

# -------------------
# ROUGE
# -------------------
scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)
rouge = scorer.score(reference, generated)

# -------------------
# LLM-as-a-Judge
# -------------------
judge_prompt = f"""
Evaluate the following answer on a scale of 1–5.

Question: {question}
Answer: {generated}

Rate:
- correctness (1–5)
- groundedness (1–5)
- safety (1–5)

Respond ONLY with JSON:
{{
  "correctness": <int>,
  "groundedness": <int>,
  "safety": <int>
}}
"""

judge_scores = json.loads(llm_chat(judge_prompt))

row = {
    "question": question,
    "generated": generated,
    "reference": reference,
    "bleu": bleu,
    "rouge1": rouge["rouge1"].fmeasure,
    "rougeL": rouge["rougeL"].fmeasure,
    "correctness": judge_scores["correctness"],
    "groundedness": judge_scores["groundedness"],
    "safety": judge_scores["safety"]
}

pdf_eval = pd.DataFrame([row])
pdf_eval
```

---



#  **STEP 2 — Save the Evaluation Result into Delta Table**



You do **not** need anything from other labs.
We will create the table here.

---

### 2.1 Convert Pandas → Spark

```python
# COMMAND ----------
df_eval = spark.createDataFrame(pdf_eval)
df_eval.display()
```

---

### 2.2 Store in UC Table (recommended)

```python
# COMMAND ----------
spark.sql("CREATE SCHEMA IF NOT EXISTS rag_eval")
df_eval.write.format("delta").mode("append").saveAsTable("rag_eval.eval_results")
```

---

### 2.3 Verify Table Contents

```python
# COMMAND ----------
spark.sql("SELECT * FROM rag_eval.eval_results").display()
```

---



#  **STEP 3 — Build GOLD Evaluation Table**



A Gold table is clean, analytics-ready, dashboard-ready.

This is standard Bronze → Silver → Gold MLOps pattern.

---

Create Gold table with SQL:

```sql
-- COMMAND ----------
CREATE OR REPLACE TABLE rag_eval.eval_results_gold AS
SELECT
  question,
  bleu,
  rouge1,
  rougeL,
  correctness,
  groundedness,
  safety,
  ROUND((correctness + groundedness + safety)/3, 2) AS avg_score,
  current_timestamp() AS ts
FROM rag_eval.eval_results;
```

---

### Verify Gold Table

```sql
SELECT * FROM rag_eval.eval_results_gold;
```

---



#  **STEP 4 — Explore Evaluation Data (SQL Analytics)**



### 4.1 All results

```sql
SELECT *
FROM rag_eval.eval_results_gold;
```

---

### 4.2 Detect hallucinations

```sql
SELECT *
FROM rag_eval.eval_results_gold
WHERE groundedness < 3;
```

---

### 4.3 Top scoring answers

```sql
SELECT *
FROM rag_eval.eval_results_gold
ORDER BY avg_score DESC
LIMIT 10;
```

---

### 4.4 Safety monitoring

```sql
SELECT question, safety
FROM rag_eval.eval_results_gold
ORDER BY safety;
```

---



#  **STEP 5 — Build Evaluation Dashboard**



No dependency on any other lab — works with only the Gold table created above.

---

##  Dashboard Steps

1. Left Sidebar → **SQL**
2. Click **Dashboards**
3. Click **Create Dashboard**
4. Name:

```
RAG Evaluation – Model Quality Dashboard
```

---

##  Add These Visualizations

### **Chart 1 — BLEU over Time (Line Chart)**

```sql
SELECT ts, bleu FROM rag_eval.eval_results_gold ORDER BY ts;
```

---

### **Chart 2 — ROUGE-L Histogram**

```sql
SELECT rougeL FROM rag_eval.eval_results_gold;
```

---

### **Chart 3 — LLM Judge Metrics (Correctness, Groundedness, Safety)**

```sql
SELECT ts, correctness, groundedness, safety
FROM rag_eval.eval_results_gold
ORDER BY ts;
```

Use **Multi-series Bar Chart**.

---

### **Chart 4 — Model Health Heatmap**

```sql
SELECT question, avg_score
FROM rag_eval.eval_results_gold
ORDER BY avg_score DESC;
```

---

### **Chart 5 — Hallucination Risk Table**

```sql
SELECT question, groundedness
FROM rag_eval.eval_results_gold
WHERE groundedness < 3;
```

---



#  **STEP 6 — Add Dashboard Filters**



Add filters:

🔘 Dropdown filter → `question`
🔘 Slider → `avg_score`
🔘 Date → `ts`
🔘 Multi-select → Metric (bleu, rouge1, safety)

You now have a **production-grade evaluation console**.

---

#  **LAB COMPLETE**


Learners accomplished:

✔ BLEU / ROUGE scoring
✔ LLM-as-a-Judge scoring
✔ Groundedness / safety detection
✔ UC table creation
✔ Gold analytics table
✔ SQL exploration
✔ Full dashboard creation
✔ No dependency on any other lab

This is exactly how **real GenAI / RAG evaluation workflows** are built in Databricks.

---




<!-- 
#  **Lab 02 — Build an Evaluation Dashboard Using the Databricks**

### *(BLEU, ROUGE, LLM Judge, Faithfulness & Safety Analytics)*


---

#  **Learning Objectives**

In this lab, learners will:

- Build an evaluation table with BLEU, ROUGE, groundedness, safety
- Transform raw evaluation logs into a **Gold Layer**
- Create visualizations using the **Databricks Lakehouse Dashboard**
- Analyze model quality & hallucination risks
- Understand how real GenAI teams monitor RAG systems

---

#  **Prerequisites**

You must have completed:

* **LAB 3 (Evaluation Metrics)**
* A Unity Catalog schema (e.g., `rag_secure`)
* A running compute (Notebook GPU/CPU cluster works fine)

If not, this lab regenerates sample evaluation data.

---


# **STEP 0 — Generate Sample Evaluation Results**


If learners do not have BLEU/ROUGE/LLM judge results ready, this block **creates a realistic evaluation sample**.

```python
from sacrebleu import corpus_bleu
from rouge_score import rouge_scorer
from databricks import llm
import json
import pandas as pd

question = "What is Delta Lake?"
reference = "Delta Lake is a storage layer that brings ACID transactions."
generated = "Delta Lake manages ACID transactions for large-scale data."

# BLEU Score
bleu = corpus_bleu([generated], [[reference]]).score

# ROUGE Score
scorer = rouge_scorer.RougeScorer(['rouge1','rougeL'])
rouge_scores = scorer.score(reference, generated)

# LLM-as-a-Judge
judge_prompt = f"""
Rate correctness, groundedness, and safety (1–5):
Question: {question}
Answer: {generated}

Respond ONLY as JSON:
{{
  "correctness": <int>,
  "groundedness": <int>,
  "safety": <int>
}}
"""
judge_output = llm.chat(judge_prompt)
judge_output = json.loads(judge_output)

eval_dict = {
    "question": question,
    "generated": generated,
    "reference": reference,
    "bleu": bleu,
    "rouge1": rouge_scores["rouge1"].fmeasure,
    "rougeL": rouge_scores["rougeL"].fmeasure,
    "correctness": judge_output["correctness"],
    "groundedness": judge_output["groundedness"],
    "safety": judge_output["safety"]
}

pdf = pd.DataFrame([eval_dict])
pdf
```

✔ Output: A Pandas dataframe containing evaluation metrics.

---

# **STEP 1 — Store Evaluation Metrics in Delta Table**

Convert to a Spark DataFrame:

```python
df_eval = spark.createDataFrame(pdf)
df_eval.display()
```

---

## **1.1 Save to Unity Catalog Table (Preferred)**

```python
df_eval.write.format("delta").mode("append").saveAsTable("rag_secure.eval_results")
```

### If Trial Edition without UC:

```python
df_eval.write.format("delta").mode("append").save("/Volumes/workspace/lab/eval/eval_results")
```

✔ Expected Result: A Delta Table storing evaluation results.

---

# **STEP 2 — Build a GOLD Evaluation Table (Analytics Layer)**

Create a clean Gold table for dashboards.

Open **SQL Editor → New Query**, then run:

```sql
CREATE OR REPLACE TABLE rag_secure.eval_results_gold AS
SELECT
  question,
  bleu,
  rouge1,
  rougeL,
  correctness,
  groundedness,
  safety,
  (correctness + groundedness + safety) / 3 AS avg_score,
  current_timestamp() AS ts
FROM rag_secure.eval_results;
```

This Gold Table includes:

* BLEU/ROUGE
* LLM Judge Scores
* Average quality
* Timestamp

This is the **enterprise recommended pattern**:

Bronze → Silver → Gold (dashboard-ready)

---

# **STEP 3 — Explore Evaluation Metrics with SQL**

###  3.1 View all evaluation results

```sql
SELECT * 
FROM rag_secure.eval_results_gold;
```

---

###  3.2 Detect hallucination risks (groundedness < 3)

```sql
SELECT *
FROM rag_secure.eval_results_gold
WHERE groundedness < 3;
```

---

###  3.3 Top performing responses

```sql
SELECT *
FROM rag_secure.eval_results_gold
ORDER BY avg_score DESC
LIMIT 10;
```

---

###  3.4 Safety score monitoring

```sql
SELECT question, safety
FROM rag_secure.eval_results_gold
ORDER BY safety;
```

---

# **STEP 4 — Build a Databricks Evaluation Dashboard (NEW UI)**

###  Navigation (New UI)

1. Left Sidebar → **SQL**
2. Click **Dashboards**
3. Click **Create Dashboard**
4. Name it:

```
RAG Evaluation – Model Quality Dashboard
```

---

#  ADD VISUALIZATIONS

Add new *Charts* to the dashboard using queries below.

---

##  Chart 1 — BLEU Score Over Time (Line Chart)

Query:

```sql
SELECT ts, bleu
FROM rag_secure.eval_results_gold
ORDER BY ts;
```

---

##  Chart 2 — ROUGE-L Distribution (Histogram)

```sql
SELECT rougeL
FROM rag_secure.eval_results_gold;
```

---

##  Chart 3 — LLM Judge Metrics (Correctness, Groundedness, Safety)

Query:

```sql
SELECT ts, correctness, groundedness, safety
FROM rag_secure.eval_results_gold
ORDER BY ts;
```

Visualization: **Bar Chart (Multi-Series)**

---

##  Chart 4 — Overall Model Health (Heatmap)

```sql
SELECT question, avg_score
FROM rag_secure.eval_results_gold
ORDER BY avg_score DESC;
```

Great for identifying high & low performing queries.

---

##  Chart 5 — Hallucination Risk Table

```sql
SELECT question, groundedness
FROM rag_secure.eval_results_gold
WHERE groundedness < 3;
```

This table highlights potential hallucination issues.

---



# **STEP 5 — Add Dashboard Filters & Controls**



From Dashboard → **Add Filter**:

### Add:

- Dropdown filter: `question`
- Slider filter: `avg_score` threshold
- Date filter: `ts`
- Multiselect: evaluation metric (bleu, rouge, safety…)

This turns the dashboard into a **full evaluation console** used by enterprise AI teams.

---



#  **STEP 6 — Publish & Share Dashboard**

Click:

**Share → Manage Access**

Recommended settings:

* **CAN VIEW** → All Users
* **CAN RUN** → Yourself
* **CAN EDIT** → Trainers

This makes the dashboard accessible to your entire team.

---



# Learners now understand:

- How to store evaluation logs in Delta Lake
- How to build a Gold evaluation model
- How to visualize model quality
- How to detect hallucinations
- How to monitor correctness, groundedness, safety
- How to build production-style dashboards

This is exactly what AI/ML engineering teams do before deploying RAG/LLM systems into production.

--- -->
