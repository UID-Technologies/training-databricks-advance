
## 🧪 Lab 1 – Getting Started with Lakeflow Jobs (What is Lakeflow Jobs?)

### 🎯 Learning Objectives

By the end of this lab, learners will:

* Understand what **Lakeflow Jobs** are in the Databricks ecosystem.
* Create a very simple **single-task job** that runs a notebook.
* View job runs and logs.

### ✅ Prerequisites

* Databricks workspace with Lakeflow enabled.
* Permission to create **jobs** and **notebooks**.
* A running cluster or access to serverless compute.

---

### Step 1 – Concept: What is Lakeflow Jobs?

> Trainer explains before hands-on:

* **Lakeflow Jobs** = Databricks’ unified **orchestration layer** for:

  * Notebooks
  * Workflows
  * Ingestion pipelines (LakeFlow Connect)
  * SQL queries, Delta Live Tables, etc.
* They define:

  * **Tasks**
  * **Dependencies between tasks**
  * **Schedules & triggers**
  * **Retries, alerts, monitoring**

Then: “Now we’ll build our very first Lakeflow Job.”

---

### Step 2 – Create a Simple Notebook to Use in the Job

1. Go to **Workspace → your user folder**.
2. Click **Create → Notebook**.
3. Name it: `job_demo_notebook`.
4. Language: **Python**.
5. Attach a running cluster.

Paste this code:

```python
from datetime import datetime

print("Lakeflow Job Demo – Notebook Task")
print("Current time:", datetime.now())

# Simulate a small “data engineering” task
df = spark.range(1, 11).toDF("id")
df = df.withColumn("id_squared", df.id * df.id)
df.show()

print("Row count =", df.count())
```

6. Run the notebook once to ensure it works.

---

### Step 3 – Open Lakeflow Jobs UI

1. In the left sidebar, click **Lakeflow**.
2. Navigate to the **Jobs** section (depending on UI, might be “Workflows / Jobs” under Lakeflow branding).
3. Click **Create job**.

---

### Step 4 – Define Your First Job

1. In the **Create job** screen:

   * Job name: `lf_job_first_demo`.
2. Add a **task**:

   * Click **Add task**.
   * Task name: `run_demo_notebook`.
   * Task type: **Notebook**.
   * Select notebook: `job_demo_notebook`.
   * Choose compute:

     * Use existing cluster or define a **job cluster** (recommended for prod, but any for lab).
3. Click **Create** / **Save**.

You should now see:

* A job with a single task box (`run_demo_notebook`).

---

### Step 5 – Run the Job Manually

1. Click **Run now** (or “Start”).
2. Watch the job state:

   * `Pending → Running → Succeeded` (hopefully 😄).
3. Click on the **latest run**:

   * Inspect **Run details**.
   * Click on the task, then on **Output / Logs**.
4. Confirm:

   * The notebook printed text.
   * The DataFrame result was shown.

---

### Step 6 – Wrap-Up Questions

Ask participants:

* How is this different from just running a notebook manually?

  * Jobs can schedule, retry, orchestrate multiple tasks.
* What else can be a job task?

  * Notebook, DLT pipeline, SQL query, ingestion pipeline, etc.

---

