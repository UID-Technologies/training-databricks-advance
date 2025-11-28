
#  **LAB 4 — LakeFlow Jobs (DLT + Notebooks + If/Else Branching)**


**Level:** Intermediate → Advanced

---

#  **Business Scenario**

Your ACADO Retail data pipeline loads files into the Bronze layer.
Before running a DLT pipeline, your LakeFlow orchestrator must:

1. **Check whether new data exists**
2. If **data exists → run DLT**
3. If **no data → skip DLT + send notification**

This prevents unnecessary DLT runs, saving compute cost and avoiding failures.

We will build:

```
Task A   Validate Data Availability
          │
          ├── READY → Task B (Run DLT)
          └── EMPTY → Task C (Send Alert)
```

---

#  **PART 1 — Create Notebook for File Count Validation (Task A)**

Create a notebook:

```
lab07_validate_bronze
```

Paste the following:

```python
from pyspark.sql.functions import *

print("Checking bronze orders_raw table...")

df = spark.read.format("delta").table("training.bronze.orders_raw")

record_count = df.count()
print(f"Bronze record count: {record_count}")

if record_count == 0:
    print("No new data found — Exiting with status: EMPTY")
    dbutils.notebook.exit("EMPTY")
else:
    print("Data available — Exiting with status: READY")
    dbutils.notebook.exit("READY")
```

### ✔ What this does

* Counts records in Bronze table
* Exits with:

  * `"READY"` → run DLT
  * `"EMPTY"` → skip DLT

This exit value becomes the **branching condition** in your workflow.

---

#  **PART 2 — Create the DLT Pipeline (Task B)**

### Step 2.1 — Build a simple DLT pipeline

Create a new DLT pipeline named:

```
orders_dlt_pipeline
```

### Use SQL or Python (here is SQL version)

**Pipeline Notebook:**

```
lab07_dlt_orders
```

Paste:

```sql
CREATE OR REFRESH STREAMING LIVE TABLE orders_bronze
AS SELECT * FROM STREAM(training.bronze.orders_raw);

CREATE OR REFRESH LIVE TABLE orders_silver
AS SELECT 
  order_id,
  customer_id,
  country,
  CAST(order_date AS DATE) AS order_date,
  CAST(amount AS DOUBLE) AS amount
FROM LIVE.orders_bronze
WHERE amount > 0;
```

### Step 2.2 — Save pipeline

Make sure target:

* Catalog: `training`
* Schema: `silver_dlt`

---

#  **PART 3 — Create Notification Notebook (Task C)**

Create:

```
lab07_notify_empty
```

Paste:

```python
print("No new files detected. Sending alert...")

# Fake alert logic (Trial has no SMTP)
message = "DLT was skipped because the source table has no new rows."

print("=== ALERT ===")
print(message)

dbutils.notebook.exit("ALERT_SENT")
```

---

#  **PART 4 — Build LakeFlow Job with Branching Logic**

Go to:

```
Workflows → Jobs → Create Job
```

Job name:

```
lab07_lakeflow_branching
```

---

## **Step 4.1 — Task A: Validate Data**

* Add task
* Task name: `check_data`
* Type: **Notebook**
* Notebook: `lab07_validate_bronze`
* Compute: **Serverless** (default)

This task returns:

* `"READY"` or `"EMPTY"`

---

## **Step 4.2 — Task B: Run DLT Pipeline**

* Add Task
* Task name → `run_dlt`
* Task type → **DLT Pipeline**
* Select → `orders_dlt_pipeline`
* Depends on → `check_data`

###  Add Condition

Click **Add Condition**:

```
Condition type: String comparison
Left value: {{tasks.check_data.result}}
Operator: equals
Right value: READY
```

Meaning:

→ Run DLT only when Task A returns `"READY"`.

---

## **Step 4.3 — Task C: Notification Task**

* Add Task
* Task name → `send_alert`
* Task type → **Notebook**
* Notebook → `lab07_notify_empty`
* Depends on → `check_data`

###  Add Condition

```
Left: {{tasks.check_data.result}}
Operator: equals
Right: EMPTY
```

Meaning:

→ If no data, send alert (skip DLT).

---

Your workflow now looks like:

```
check_data
     │
     ├── READY  → run_dlt
     └── EMPTY  → send_alert
```

---

#  **PART 5 — Test the Workflow**

## Case 1 — Bronze Table Has Data

Run:

```sql
SELECT COUNT(*) FROM training.bronze.orders_raw;
```

If > 0, then:

* Task A → READY
* Task B (DLT) → runs
* Task C → skipped

## Case 2 — Empty Bronze Table

Clear table with:

```sql
DELETE FROM training.bronze.orders_raw WHERE TRUE;
```

Run job again:

* Task A → EMPTY
* Task B → skipped
* Task C → ALERT_SENT

---

#  **PART 6 — Validate DLT Output**

If DLT ran (READY case):

```sql
SELECT COUNT(*) FROM training.silver_dlt.orders_silver;
```

If skipped (EMPTY case):

```sql
SELECT 'DLT SKIPPED - NO NEW DATA';
```

---

#  **PART 7 — Add Job Notifications (Optional)**

In the Job:

```
Settings → Notifications
```

Add:

* **On Failure → Email**
* **On Success → None**
* **On Skip → Email (optional)**

---

#  **LAB  COMPLETE — What You Learned**

You created an enterprise-level pipeline using:

✔ Notebook validation logic
✔ dbutils.notebook.exit()
✔ LakeFlow conditional branching (if/else)
✔ Combining DLT + Notebooks + Alerts
✔ Safe & cost-efficient pipeline design

This is how Fortune-500 teams orchestrate:

* Real-time ingestion
* Automatic validation
* Conditional logic
* Automated alerting
* DLT pipelines

---

