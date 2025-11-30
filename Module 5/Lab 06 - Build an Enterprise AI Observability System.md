#  **LAB 06 — Build an Enterprise AI Observability System (Standalone Edition)**

### *(Telemetry ▸ Monitoring ▸ Evaluation ▸ Drift)*

---

#  **Learning Objectives**

By the end of this standalone lab, learners will build:

✔ A **Telemetry Logging Layer**
✔ An **Evaluation Pipeline (BLEU, ROUGE, LLM Judge)**
✔ A **Model Drift Detection System**
✔ A **Databricks Observability Dashboard**
✔ Automation using **Workflows → Jobs**

This lab simulates real enterprise observability for AI systems.

---



#  **Enterprise Observability Architecture**

```
                   ┌───────────────────────┐
                   │    User / App Layer    │
                   └───────────────────────┘
                               ↓
                   ┌───────────────────────┐
                   │     Telemetry Logs     │
                   │  (Requests + Responses)│
                   └───────────────────────┘
                               ↓
                   ┌───────────────────────┐
                   │  Evaluation Metrics    │
                   │ (BLEU, ROUGE, Judge)   │
                   └───────────────────────┘
                               ↓
                   ┌───────────────────────┐
                   │   Drift Detection      │
                   │ (Quality/Latency Drift)│
                   └───────────────────────┘
                               ↓
                   ┌───────────────────────┐
                   │ Observability Dashboard│
                   └───────────────────────┘
                               ↓
                   ┌───────────────────────┐
                   │  Alerts & Automation   │
                   └───────────────────────┘
```

---


#  **STEP 0 — Notebook Setup (Standalone)**

Create notebook:

```
06_ai_observability_standalone
```

---

### 0.1 Install Dependencies

```python
%pip install sacrebleu rouge-score
dbutils.library.restartPython()
```

---

### 0.2 Import All Required Libraries

```python
import json, uuid, time
from datetime import datetime

import pandas as pd
from sacrebleu import corpus_bleu
from rouge_score import rouge_scorer

import requests
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()
```

---

#  **STEP 1 — Synthetic Data (Standalone)**

We generate **self-contained** dataset of:

* 5 questions
* 5 references
* 5 simulated model responses
* Simulated "context"

### 1.1 Create Synthetic Questions / References / Model Outputs

```python
questions = [
    "What is Delta Lake?",
    "Explain ACID transactions.",
    "What is a Data Lakehouse?",
    "Define machine learning.",
    "Explain what a feature store is."
]

references = {
    "What is Delta Lake?": "Delta Lake is a storage layer that brings ACID transactions to data lakes.",
    "Explain ACID transactions.": "ACID stands for Atomicity, Consistency, Isolation, Durability.",
    "What is a Data Lakehouse?": "A Lakehouse combines data lakes and warehouses into one platform.",
    "Define machine learning.": "Machine learning is the field of study where systems learn from data.",
    "Explain what a feature store is.": "A feature store centralizes and manages ML features for training and serving."
}

# Simulated model outputs (imperfect on purpose)
model_outputs = {
    "What is Delta Lake?": "Delta Lake is a technology that helps manage data reliably.",
    "Explain ACID transactions.": "ACID includes atomicity and consistency rules.",
    "What is a Data Lakehouse?": "Lakehouse is an architecture for modern data.",
    "Define machine learning.": "Machine learning means systems learn from examples.",
    "Explain what a feature store is.": "A feature store is useful for machine learning pipelines."
}
```

This makes the lab fully functional without external data.

---

#  **STEP 2 — Telemetry Logging Layer**

We log:

* question
* response
* latency
* model name
* context size

### 2.1 Create Telemetry Table (Standalone)

```python
spark.sql("CREATE SCHEMA IF NOT EXISTS ai_obs")

spark.sql("""
CREATE TABLE IF NOT EXISTS ai_obs.telemetry_logs (
    id STRING,
    timestamp TIMESTAMP,
    question STRING,
    model STRING,
    context_length INT,
    latency_sec DOUBLE,
    response STRING
) USING delta
""")
```

---

### 2.2 Telemetry Logging Function

```python
def log_telemetry(question, response, latency, context):
    df = spark.createDataFrame([{
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "question": question,
        "model": "simulated-model-v1",
        "context_length": len(context),
        "latency_sec": latency,
        "response": response
    }])
    
    df.write.format("delta").mode("append").saveAsTable("ai_obs.telemetry_logs")
```

---

#  **STEP 3 — Evaluation Metrics Layer**

We compute:

* BLEU
* ROUGE-1
* ROUGE-L
* LLM Judge (mocked to keep standalone)

### 3.1 Setup Evaluators

```python
scorer = rouge_scorer.RougeScorer(["rouge1","rougeL"])
```

---

### 3.2 Mocked LLM Judge (Standalone Safe)

No Databricks endpoint required — fully local.

```python
def llm_judge(question, answer):
    # Simulated correctness (randomized)
    import random
    return {
        "correctness": random.randint(3,5),
        "groundedness": random.randint(2,5),
        "safety": 5   # assume safe, as synthetic
    }
```

---

### 3.3 Create Evaluation Logs Table

```python
spark.sql("""
CREATE TABLE IF NOT EXISTS ai_obs.evaluation_logs (
    id STRING,
    timestamp TIMESTAMP,
    question STRING,
    bleu DOUBLE,
    rouge1 DOUBLE,
    rougeL DOUBLE,
    correctness INT,
    groundedness INT,
    safety INT,
    avg_quality DOUBLE
) USING delta
""")
```

---

### 3.4 Evaluation Logger

```python
import sacrebleu
from rouge_score import rouge_scorer
from nltk.translate.bleu_score import corpus_bleu
scorer = rouge_scorer.RougeScorer(['rouge1', 'rougeL'], use_stemmer=True)

def log_evaluation(question, answer, reference):
    bleu = corpus_bleu([answer], [[reference]])
    rouge = scorer.score(reference, answer)
    judge = llm_judge(question, answer)

    avg_quality = (
        judge["correctness"] 
        + judge["groundedness"] 
        + judge["safety"]
    ) / 3

    # Create DataFrame row
    df = spark.createDataFrame([{
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "question": question,
        "bleu": float(bleu),
        "rouge1": float(rouge["rouge1"].fmeasure),
        "rougeL": float(rouge["rougeL"].fmeasure),
        "correctness": int(judge["correctness"]),
        "groundedness": int(judge["groundedness"]),
        "safety": int(judge["safety"]),
        "avg_quality": float(avg_quality)
    }])

    # Explicit casting to prevent schema merge conflicts
    columns_to_cast = {
        "correctness": "integer",
        "groundedness": "integer",
        "safety": "integer"
    }

    for col, dtype in columns_to_cast.items():
        df = df.withColumn(col, df[col].cast(dtype))

    # Safe write
    df.write.format("delta").mode("append").saveAsTable("ai_obs.evaluation_logs")
```

---

#  **STEP 4 — Full Observability Pipeline (Standalone)**

```python
def run_observability_pipeline(question):
    reference = references[question]
    synthetic_response = model_outputs[question]

    # simulate latency
    start = time.time()
    time.sleep(0.2)
    latency = time.time() - start

    # Telemetry log
    log_telemetry(
        question,
        synthetic_response,
        latency,
        context=reference
    )

    # Evaluation log
    log_evaluation(
        question,
        synthetic_response,
        reference
    )

    return synthetic_response
```

---

#  **STEP 5 — Run for All Questions**

```python
for q in questions:
    print("Evaluating:", q)
    print(run_observability_pipeline(q))
    print("----")
```

---

#  **STEP 6 — Build Drift Table (Standalone)**

```sql
CREATE OR REPLACE TABLE ai_obs.quality_drift AS
SELECT
  date(timestamp) AS day,
  AVG(avg_quality) AS avg_score
FROM ai_obs.evaluation_logs
GROUP BY day
ORDER BY day;
```

---

#  **STEP 7 — Drift Detection Query**

```sql
SELECT 
  day,
  avg_score,
  LAG(avg_score) OVER (ORDER BY day) AS prev_score,
  avg_score - LAG(avg_score) OVER (ORDER BY day) AS drift
FROM ai_obs.quality_drift;
```

Add alert when:

```
avg_score < 3.5
```

---

#  **STEP 8 — Build Observability Dashboard (Standalone)**

Create dashboard and add these queries:

---

###  1. Average Quality Over Time (Line Chart)

```sql
SELECT * FROM ai_obs.quality_drift;
```

---

###  2. BLEU / ROUGE Trends

```sql
SELECT timestamp, bleu, rouge1, rougeL
FROM ai_obs.evaluation_logs
ORDER BY timestamp;
```

---

###  3. Latency Monitoring

```sql
SELECT timestamp, latency_sec
FROM ai_obs.telemetry_logs
ORDER BY timestamp;
```

---

###  4. Question-Level Heatmap

```sql
SELECT question, avg_quality
FROM ai_obs.evaluation_logs;
```

---

###  5. Telemetry Table

```sql
SELECT * FROM ai_obs.telemetry_logs;
```

---

#  **STEP 9 — Automate with Databricks Jobs**

Create job:

```
ai_observability_job
```

Tasks:

1. `generate_synthetic_activity`
2. `run_observability_pipeline`
3. `drift_analysis`

Schedule:
**Every 1 hour**

Add alert:
**When avg_score < 3.5**

---

#  **LAB COMPLETE — You Built a Standalone AI Observability Platform**

This lab now:

✔ Runs fully standalone
✔ Generates its own synthetic questions, references, responses
✔ Logs telemetry & evaluation
✔ Computes drift
✔ Builds analytics dashboard
✔ Supports automated jobs










<!-- 
#  **LAB 06 — Build an Enterprise AI Observability System**

### *(Telemetry ▸ Monitoring ▸ Evaluation ▸ Drift)*

---

#  **Learning Objectives**

By the end of this lab, you will:

✔ Build a **Telemetry Logging Layer** for RAG / LLM apps
✔ Track user queries, model outputs, latency, evaluation scores
✔ Detect **model drift** across BLEU, ROUGE, correctness, groundedness
✔ Build an **AI Observability Dashboard** in Databricks
✔ Configure **alerts** for anomaly detection
✔ Implement a **continuous monitoring job**
✔ Gain enterprise-level visibility into LLM/RAG health

This is exactly what companies build for **production AI reliability**.

---

#  **Enterprise Observability Architecture**

```
                   ┌───────────────────────┐
                   │    User / App Layer    │
                   └───────────────────────┘
                               ↓
                   ┌───────────────────────┐
                   │     Telemetry Logs     │
                   │  (Requests + Responses)│
                   └───────────────────────┘
                               ↓
                   ┌───────────────────────┐
                   │  Evaluation Metrics    │
                   │ (BLEU, ROUGE, Judge)   │
                   └───────────────────────┘
                               ↓
                   ┌───────────────────────┐
                   │   Drift Detection      │
                   │ (Quality/Latency Drift)│
                   └───────────────────────┘
                               ↓
                   ┌───────────────────────┐
                   │ Observability Dashboard│
                   └───────────────────────┘
                               ↓
                   ┌───────────────────────┐
                   │  Alerts & Automation   │
                   └───────────────────────┘
```

---



#  **STEP 0 — Notebook Setup**



Create notebook:

```
11_ai_observability
```

Install dependencies:

```python
%pip install sacrebleu rouge-score
dbutils.library.restartPython()
```

Imports:

```python
from databricks import llm
import pandas as pd
import numpy as np
import time, uuid, json
from sacrebleu import corpus_bleu
from rouge_score import rouge_scorer
from datetime import datetime
```

---


#  **STEP 1 — Create Telemetry Logging Layer**


This logs **every LLM/RAG request**:

* question
* context size
* model used
* latency
* raw response
* timestamp

### 1.1 Define Telemetry Function

```python
def log_telemetry(question, model, context, response, latency):
    df = spark.createDataFrame([{
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "question": question,
        "context_length": len(context),
        "model": model,
        "latency_sec": latency,
        "response": response
    }])

    df.write.format("delta").mode("append") \
        .saveAsTable("rag_secure.telemetry_logs")
```

---


#  **STEP 2 — Add Real-Time RAG Evaluation Inside Telemetry Pipeline**


BLEU/ROUGE setup:

```python
scorer = rouge_scorer.RougeScorer(["rougeL", "rouge1"])
```

LLM-as-a-Judge setup:

```python
def llm_judge(question, answer):
    judge_prompt = f"""
Rate correctness, groundedness and safety (1-5).
Return JSON only: {{"correctness":X, "groundedness":Y, "safety":Z}}

Question: {question}
Answer: {answer}
"""
    return json.loads(llm.chat(judge_prompt))
```

---

### 2.1 Combined Evaluation Logger

```python
def log_evaluation(question, answer, reference):
    bleu = corpus_bleu([answer], [[reference]]).score
    rouge = scorer.score(reference, answer)
    judge = llm_judge(question, answer)

    df = spark.createDataFrame([{
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(),
        "question": question,
        "bleu": bleu,
        "rouge1": rouge["rouge1"].fmeasure,
        "rougeL": rouge["rougeL"].fmeasure,
        "correctness": judge["correctness"],
        "groundedness": judge["groundedness"],
        "safety": judge["safety"],
        "avg_quality": (judge["correctness"] + judge["groundedness"] + judge["safety"]) / 3
    }])

    df.write.format("delta").mode("append") \
        .saveAsTable("rag_secure.evaluation_logs")
```

---

#  **STEP 3 — Build Real-Time RAG Pipeline with Telemetry**


Load embeddings & chunks:

```python
df_chunks = spark.read.load("/Volumes/workspace/lab/myvolume/prepared_chunks")
local = df_chunks.toPandas()
chunks = local["chunk"].tolist()
vectors = np.array(local["embedding"].tolist()).astype("float32")

from sentence_transformers import SentenceTransformer
embedder = SentenceTransformer("all-MiniLM-L6-v2")
```

---

### 3.1 RAG with Observability

```python
def rag_inference(question, model_name="dbrx"):
    # build context
    q_emb = embedder.encode(question)
    sims = np.dot(vectors, q_emb)
    top = np.argsort(sims)[::-1][:3]
    context = "\n".join([chunks[i] for i in top])

    # build prompt
    prompt = f"""
Use ONLY this context:
{context}

Question: {question}
"""

    # call model
    start = time.time()
    response = llm.chat(prompt) if model_name=="dbrx" else llm.chat(prompt, model=model_name)
    latency = time.time() - start

    # log telemetry
    log_telemetry(question, model_name, context, response, latency)

    return response, context
```

---

### 3.2 Full Inference + Evaluation

```python
def rag_with_observability(question):
    response, context = rag_inference(question, "dbrx")

    # reference answers (defined earlier)
    reference = reference_answers.get(question, "")

    log_evaluation(question, response, reference)

    return response
```

---



#  **STEP 4 — Run Observability Pipeline**

Example run:

```python
rag_with_observability("What is Delta Lake?")
rag_with_observability("Explain ACID transactions.")
```

Check tables:

```sql
SELECT * FROM rag_secure.telemetry_logs;
SELECT * FROM rag_secure.evaluation_logs;
```

---


#  **STEP 5 — Drift Detection (Model Quality Drift)**


Define drift thresholds:

```python
DRIFT_THRESHOLD = 0.15
```

Compute average quality per day:

```sql
CREATE OR REPLACE TABLE rag_secure.quality_drift AS
SELECT
  date(timestamp) AS day,
  AVG(avg_quality) AS avg_score
FROM rag_secure.evaluation_logs
GROUP BY day
ORDER BY day;
```

Detect drift:

```sql
SELECT 
  day,
  avg_score,
  LAG(avg_score,1) OVER (ORDER BY day) AS prev_score,
  (avg_score - LAG(avg_score,1) OVER (ORDER BY day)) AS drift
FROM rag_secure.quality_drift;
```

---

### Drift Alert Rule

Add SQL:

```sql
SELECT *
FROM rag_secure.quality_drift
WHERE avg_score < 0.7;  -- your threshold
```

Add Dashboard alert:
**Notify when avg_score < 0.7**

---

#  **STEP 6 — Build AI Observability Dashboard (New UI)**

Dashboard sections:

##  1. Quality Metrics Over Time

Query:

```sql
SELECT day, avg_score FROM rag_secure.quality_drift;
```

Chart: Line chart

---

##  2. BLEU/ROUGE Trends

```sql
SELECT timestamp, bleu, rougeL
FROM rag_secure.evaluation_logs;
```

---

##  3. Latency Monitoring

```sql
SELECT timestamp, model, latency_sec
FROM rag_secure.telemetry_logs;
```

---

##  4. Drift Heatmap

```sql
SELECT question, avg_quality
FROM rag_secure.evaluation_logs;
```

---

##  5. Safety Violations

If integrated with LAB 8 Guardrails:

```sql
SELECT timestamp, question, answer
FROM rag_secure_audit.guardrail_logs
ORDER BY timestamp DESC;
```

---


#  **STEP 7 — Automate Observability Pipeline Using Jobs**

Create Job:

```
ai_observability_job
```

Tasks:

1. **run_rag_eval** (LAB 5)
2. **eval_metrics**
3. **11_ai_observability**

Add schedule:
**Every 2 hours**

Add email alert:
**On failure or drift detection**

---

# **Lab Complete — You Built an Enterprise AI Observability System!**


You now have:

✔ Full telemetry logging
✔ Evaluation pipelines
✔ Model quality tracking
✔ Latency monitoring
✔ Safety & PII monitoring
✔ Drift detection logic
✔ Observability dashboards
✔ Automated jobs
✔ End-to-end enterprise AI governance

This is **exactly** what companies deploy for:

* RAG production
* Multi-agent orchestration
* Financial/Legal AI assistants
* Safety-critical AI systems
* LLM governance & compliance

--- -->
