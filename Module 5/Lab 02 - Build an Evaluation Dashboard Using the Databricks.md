
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

---
