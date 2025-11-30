
#  **MODULE 1 — Data Legality & Guardrails**

---

#  **Topic Explanation — Why Evaluate GEN AI Applications**

Enterprise GEN AI applications must comply with:

* **Data privacy laws** (GDPR, HIPAA, DPDP India Act)
* **Intellectual property rules**
* **Customer privacy**
* **Sensitive data boundaries**
* **Confidential document handling policies**

GEN AI models **hallucinate**, and may:

* Reveal private info
* Generate harmful content
* Misinterpret instructions
* Act with bias

So **safety evaluation** is mandatory.

---

#  **Prompts & Guardrail Basics**

Guardrails = **rules + filters** that control:

* What users can ask
* What AI can answer
* How AI should behave
* What content is off-limits
* How to avoid hallucinations

These can be implemented via:

* Prompt engineering
* Moderation filters
* RAG constraints (“Use ONLY provided context”)
* Policy-based routing
* Response sanitization

Databricks supports implementing guardrails using:

* LLM Orchestration
* Notebook utilities
* MLflow model scoring
* Custom logic in Python

---

#  **LAB 1 — Build a Basic Prompt Guardrail System (Trial Edition Compatible)**

###  **Learning Objectives**

* Understand guardrail prompts
* Block unsafe requests
* Filter user inputs
* Control LLM answers

---

## **STEP 0 — Setup (Databricks Notebook)**

```python
allowed_topics = ["databricks", "delta lake", "mlflow", "rag", "unity catalog"]

def is_safe_prompt(prompt):
    # very simple guardrail logic
    banned = ["hack", "attack", "password", "virus", "illegal", "personal data"]
    return not any(word in prompt.lower() for word in banned)
```

---

## **STEP 1 — Prompt Gatekeeping**

```python
def safe_user_prompt(user_query):
    if not is_safe_prompt(user_query):
        return "❌ This question violates AI safety guardrails."
    return user_query
```

Try:

```python
safe_user_prompt("how to hack a bank server?")
safe_user_prompt("what is delta lake?")
```

---

## **STEP 2 — Add a Safety Prompt Wrapper**

```python
def safety_wrapper(prompt):
    return f"""
You must follow safety rules:
1. Do not provide harmful or illegal advice.
2. Use only factual, verifiable content.
3. If unsure, say 'I don't know.'

User Query: {prompt}
"""
```

---

## **STEP 3 — Test LLM with Safety Wrapper (Trial Edition DBRX)**

```python
from databricks import llm

query = "Explain Delta Lake"
safe_prompt = safety_wrapper(query)
llm.chat(safe_prompt)
```

---

## **Expected Output**

A safe, compliant answer.

---


# **MODULE 2 — Securing & Governing AI Systems**


#  **Topic Explanation — AI System Security**

Security concerns for GEN AI:

* Input injection
* Output poisoning
* Prompt hijacking
* Sensitive data leakage
* Model inversion attacks
* Unauthorized API usage
* Over-permissive access

Databricks handles this with:

* Unity Catalog (data governance)
* Cluster isolation
* Model Serving tokens
* Workspace access control
* Secrets API
* Audit logs
* UC-based AI asset governance

---

#  **DASF Framework (Databricks AI Security Framework)**

DASF = **Databricks AI Security Framework**

It defines:

### 1. **Data Security**

* Protecting raw PDFs, documents
* UC permissions
* PII masking

### 2. **Access Control**

* Service principals
* Cluster policies
* Token management

### 3. **System Hardening**

* Guardrails
* Prompt sanitization
* Allowed Tools Only

### 4. **Feedback Loop**

* Evaluation
* Monitoring
* Human approval

---

#  **LAB 2 — Secure Your RAG System**

###  Learning Objectives

* Use Unity Catalog access controls
* Restrict data
* Use Databricks secrets
* Protect LLM API access

---

# **STEP 1 — Create a Secure Schema (New UI)**

In **Data** → **Create Schema**:

Name:

```
rag_secure
```

Set permissions:

```
GRANT USAGE, SELECT ON SCHEMA rag_secure TO current_user;
```

---

# **STEP 2 — Create a Secret Scope**

Notebook:

```python
dbutils.secrets.createScope("rag_secrets")
```

Store an API key:

```
dbutils.secrets.put("rag_secrets", key="api_token", string_value="YOUR-TOKEN")
```

---

# **STEP 3 — Use Secret Instead of Exposing Token**

```python
import requests
token = dbutils.secrets.get("rag_secrets", "api_token")
```

---

# **STEP 4 — Secure Your RAG Pipeline**

Add input sanitization:

```python
def sanitized_query(q):
    blocked = ["hack", "breach", "attack"]
    if any(x in q.lower() for x in blocked):
        return "Blocked due to policy violation."
    return q.strip()
```

---


#  **MODULE 3 — GEN AI Evaluation Techniques**

Evaluating GEN AI systems = **mandatory in enterprise**.

We need to measure:

* Accuracy
* Faithfulness
* Safety
* Groundedness
* Completeness
* Consistency

---

#  Techniques Covered

### 1. **BLEU**

Measures precision of machine-translated text.

### 2. **ROUGE**

Measures recall for summarization.

### 3. **Mosaic AI Gauntlet**

Databricks framework for evaluating LLMs across dozens of tasks.

### 4. **MLflow LLM Evaluation**

Native MLflow evaluation APIs for LLMs.

### 5. **LLM as a Judge**

Using an LLM to grade other LLM outputs.

---

#  **LAB 3 — Evaluate Your RAG Application**

---

#  **STEP 0 — Install Packages**

```python
%pip install evaluate rouge-score sacrebleu
dbutils.library.restartPython()
```

---

#  **STEP 1 — BLEU Score Example**

```python
from sacrebleu import corpus_bleu

reference = ["Delta Lake is a storage layer that brings ACID transactions"]
generated = ["Delta Lake helps manage data with ACID properties"]

bleu = corpus_bleu(generated, [reference])
bleu.score
```

---

#  **STEP 2 — ROUGE Score Example**

```python
from rouge_score import rouge_scorer

scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"])

scores = scorer.score(reference[0], generated[0])
scores
```

---

#  **STEP 3 — MLflow LLM Evaluation (Trial Edition Works)**

```python
import mlflow
from mlflow.metrics import evaluate

eval_result = evaluate(
    model="llama3",
    data={"input": ["What is Delta Lake?"], "output": ["Delta Lake is..."]},
    evaluators=["default"]
)

eval_result
```

---

#  **STEP 4 — LLM as a Judge (Databricks DBRX)**

```python
from databricks import llm

def evaluate_answer(question, answer):
    judge_prompt = f"""
You are an evaluation judge.

Question: {question}
Answer: {answer}

Rate the answer 1–5 for:
- correctness
- groundedness
- completeness
- safety

Respond ONLY as JSON: {{"score": X}}
"""
    return llm.chat(judge_prompt)

evaluate_answer("What is MLflow?", "MLflow is a tracking tool.")
```
