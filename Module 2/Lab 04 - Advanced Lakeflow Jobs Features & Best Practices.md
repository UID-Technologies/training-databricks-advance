## 🧪 Lab 4 – Advanced Lakeflow Jobs Features & Best Practices

### 🎯 Learning Objectives

Learners will:

* Configure **conditional tasks**.
* Understand **iterative / looping patterns** (e.g., per-table tasks).
* Configure **retries & failure behavior**.
* Discuss **production best practices**.

### ✅ Prerequisites

* Job `lf_job_etl_pipeline` with multiple tasks.
* Some comfort with editing tasks.

---

### Part A – Conditional Tasks

We simulate:

* Only run `report` if `validation` passes.

> Depending on UI: some versions let you choose “run only on success / failure / always”. Use that.

### Step A.1 – Explore Conditional Task Options

1. Open the `report` task configuration.
2. Look for **“Run if” / “Condition” / “Continue if”**:

   * Set to **Run only if previous task succeeded** (SUCCESS condition).
3. Explain:

   * You can also configure tasks to run on FAILURE (e.g., send alert).

---

### Part B – Handling Task Failures & Retries

### Step B.1 – Configure Retries

1. Go to `bronze_ingest` task.
2. Set **Max retries = 3**.
3. Set **Min retry interval** (if available) – e.g., 1 minute.

Explain:

* If ingestion fails due to transient error (network, service flaky), retries can self-heal.

---

### Step B.2 – Introduce a Controlled Failure

1. Temporarily modify `lf_bronze_ingest` notebook:

   ```python
   raise Exception("Simulating ingestion failure for retry demo")
   ```

2. Run the job.

3. Watch:

   * `bronze_ingest` attempt, fail, retry.
   * Job eventually **fails** after retry limit.

4. Restore original `lf_bronze_ingest` code afterwards.

---

### Part C – Iterative / “Loop” Style Jobs (Conceptual Implementation)

Full loops are usually modelled as:

* A **single task** that loops inside the notebook over a list (e.g., table names).
* Or a **dynamic task generation** pattern (if supported by your LakeFlow version).

Simple demo in `lf_bronze_ingest` notebook:

```python
tables_to_process = ["orders", "customers", "products"]

for tbl in tables_to_process:
    print(f"Processing table {tbl}")
    # Simulate: read, transform, write
    # In real life, you'd parameterize paths & logic
```

Explain:

* This is an **iterative pattern inside a task**, not multiple tasks.
* For many independent pipelines, consider **modular jobs** or **job-per-domain**.

---

### Part D – Lakeflow Jobs in Production & Best Practices

Have participants **write notes** while you explain, and then:

#### Best Practices Checklist (Trainer-led discussion)

1. **Use job clusters** for isolation & cost control.
2. **Parameterize** notebooks for dev/test/prod.
3. Keep tasks:

   * Small, **single-responsibility**.
4. Always add:

   * **Timeouts**
   * **Retries**
   * **Alerts** (email / webhook / Slack).
5. Capture:

   * **Audit logs** (who ran what when).
   * **Metrics** (rows processed, time taken).
6. Use meaningful names:

   * `ingest_bronze_customers`, `transform_silver_orders`, etc.

You can turn this into a short **written exercise**:

> “Write a production-ready job design for your own pipeline, listing:
>
> * Tasks
> * Dependencies
> * Retry strategy
> * Schedule
> * Alerting rules”

---
