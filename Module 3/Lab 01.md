
# **LAB 01 — Install Python Libraries in Job Task (Not on Compute) + Environment Isolation Verification**

**Designed for Databricks Managed Trial / Serverless Compute**

This is the *most complete, enterprise-grade* lab on Job-Scoped Libraries—
with *multi-task workflow*, *different dependencies*, and *environment isolation verification*.

---

#  **Real Business Scenario**

You work at **Acado Retail**.
Your nightly analytics pipeline has 3 stages:

1. **Task A – Data Preparation**

   * Uses: `pandas`, `numpy`
2. **Task B – ML Scoring**

   * Uses: `pandas`, `scikit-learn`
3. **Task C – Notifications**

   * Uses: `pydantic`, `pandas`

Company Policy:

✔ Do NOT install libraries on compute
✔ Each job task must run in its own isolated dependency environment
✔ No shared cluster libraries allowed

You will build this pipeline using **Job-Scoped PyPI Libraries**.

---

#  **Part 0 — Create Three Notebooks**

Create these notebooks:

* `lab04_task_a_extract_prepare`
* `lab04_task_b_ml_scoring`
* `lab04_task_c_notify`

We will fill them step-by-step.

---

# ** Part 1 — Create a Multi-Task Job**

1. Go to **Workflows → Jobs**
2. Click **Create Job**
3. Name it:

```
lab04_job_task_libraries
```

---

## **Step 1.1 — Add Task A**

* Click **Add Task**
* Task name: `extract_prepare`
* Type: **Notebook**
* Notebook: `lab04_task_a_extract_prepare`
* Compute: **Serverless (default)**

---

## **Step 1.2 — Add Task B**

* Add Task
* Task name: `ml_scoring`
* Notebook: `lab04_task_b_ml_scoring`
* Depends on: `extract_prepare`

---

## **Step 1.3 — Add Task C**

* Add Task
* Task name: `notification`
* Notebook: `lab04_task_c_notify`
* Depends on: `ml_scoring`

Your pipeline:

```
extract_prepare  →  ml_scoring  →  notification
```

---

# **Part 2 — Add Job-Scoped Libraries Per Task**

We intentionally use **different library versions** to prove environment isolation.

---

## **Task A — Libraries**

Add PyPI libraries:

```
pandas==1.5.3
numpy==1.26.4
```

---

## **Task B — Libraries**

Add PyPI libraries:

```
pandas==2.2.2
scikit-learn==1.5.0
```

---

## **Task C — Libraries**

Add PyPI libraries:

```
pydantic==2.8.2
pandas==2.1.0
```

---

# **Part 3 — Add Environment Verification Code (Critical)**

To prove that environments differ, each notebook starts with:

## **Environment Verification Header (copy this into ALL notebooks)**

```python
import platform, sys, pkg_resources, hashlib

print("---- ENVIRONMENT CHECK ----")
print("Python version:", platform.python_version())
print("Environment prefix:", sys.prefix)

# fingerprint env
installed = sorted([f"{p.key}=={p.version}" for p in pkg_resources.working_set])
env_fingerprint = hashlib.md5("\n".join(installed).encode()).hexdigest()

print("Installed packages:", len(installed))
print("Environment hash:", env_fingerprint)
print("First 10 packages:", installed[:10])
```

This tells you:

* Unique environment path
* Different installed packages
* Environment hash (unique per task)

---

# **Part 4 — Fill Each Task Notebook**

#  **Task A Notebook — `lab04_task_a_extract_prepare`**

**Purpose: Generate synthetic daily sales and store Bronze table.**

```python
# --- ENV CHECK HEADER ---
import platform, sys, pkg_resources, hashlib

print("---- ENVIRONMENT CHECK (TASK A) ----")
installed = sorted([f"{p.key}=={p.version}" for p in pkg_resources.working_set])
print("Pandas version (Task A):", __import__("pandas").__version__)
print("NumPy version:", __import__("numpy").__version__)
print("Environment prefix:", sys.prefix)


# --- BUSINESS LOGIC ---
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("Task A - Extract & Prepare")

yesterday = datetime.now().date() - timedelta(days=1)
rng = np.random.default_rng(42)

df = pd.DataFrame({
    "order_id": np.arange(1, 1001),
    "order_date": [yesterday]*1000,
    "customer_id": rng.integers(1,500,1000),
    "country": rng.choice(["US","IN","UK","DE","FR"],1000),
    "amount": rng.normal(100,20,1000).round(2)
})

print("Sample of generated data:")
display(df.head())

spark_df = spark.createDataFrame(df)
spark_df.write.format("delta").mode("overwrite").saveAsTable("training.bronze.daily_sales")

print("Saved training.bronze.daily_sales")
```

---

#  **Task B Notebook — `lab04_task_b_ml_scoring`**

**Purpose: Train ML model + generate predictions (Silver layer).**

```python
# --- ENV CHECK HEADER ---
import platform, sys, pkg_resources, hashlib

print("---- ENVIRONMENT CHECK (TASK B) ----")
installed = sorted([f"{p.key}=={p.version}" for p in pkg_resources.working_set])
print("Pandas version (Task B):", __import__("pandas").__version__)
print("Sklearn version:", __import__("sklearn").__version__)
print("Environment prefix:", sys.prefix)


# --- BUSINESS LOGIC ---
print("Task B - ML Scoring")

df = spark.table("training.bronze.daily_sales")
pdf = df.toPandas()

from sklearn.linear_model import LinearRegression

model = LinearRegression()
model.fit(pdf[["customer_id"]], pdf["amount"])

pdf["predicted_amount"] = model.predict(pdf[["customer_id"]]).round(2)

pred_spark = spark.createDataFrame(pdf)
pred_spark.write.mode("overwrite").format("delta").saveAsTable("training.silver.daily_sales_scored")

print("Saved training.silver.daily_sales_scored")
```

---

#  **Task C Notebook — `lab04_task_c_notify`**

**Purpose: Summaries from Silver + Pydantic validation.**

```python
# --- ENV CHECK HEADER ---
import platform, sys, pkg_resources

print("---- ENVIRONMENT CHECK (TASK C) ----")
print("Pandas version (Task C):", __import__("pandas").__version__)
print("Pydantic version:", __import__("pydantic").__version__)
print("Environment prefix:", sys.prefix)


# --- BUSINESS LOGIC ---
print("Task C - Notifications")

df = spark.table("training.silver.daily_sales_scored")
pdf = df.toPandas()

summary = {
    "row_count": int(len(pdf)),
    "avg_amount": float(pdf["amount"].mean()),
    "avg_predicted": float(pdf["predicted_amount"].mean())
}

from pydantic import BaseModel

class Notification(BaseModel):
    job: str
    status: str
    metrics: dict

payload = Notification(
    job="lab04_job_task_libraries",
    status="SUCCESS",
    metrics=summary
)

print("Notification payload:")
print(payload.json(indent=2))
```

---

# **Part 5 — Run Job and Validate Environment Isolation**

### Step 5.1 — Run entire workflow

Click **Run Now**

### Step 5.2 — Open each task output

You should see:

### ✔ Task A

* pandas == **2.2.2**
* numpy == **1.26.4**
* env hash: `abc123...`

### ✔ Task B

* pandas == **2.2.2**
* scikit-learn == **1.5.0**
* env hash: `9dd8f1...` (different!)

### ✔ Task C

* pydantic == **2.8.2**
* pandas == **2.1.0**
* env hash: `7c22aa...` (again different!)

###  **This proves each task has its own isolated Python environment.**

---

# **Part 6 — SQL Validation (Optional)**

```sql
SELECT COUNT(*) FROM training.bronze.daily_sales;
```

```sql
SELECT COUNT(*), AVG(amount), AVG(predicted_amount)
FROM training.silver.daily_sales_scored;
```

---

# **LAB COMPLETED — What You Learned**

You built a **real production pipeline** and learned:

✔ How to install PyPI libraries **per task**
✔ How Serverless Compute isolates environments
✔ How each task runs with *its own dependency versions*
✔ How to verify environment differences using:

* version checks
* environment prefixes
* environment hash
* installed package list
  ✔ How to structure a 3-task workflow with different dependencies

This is Databricks-best-practice for dependency isolation.

--