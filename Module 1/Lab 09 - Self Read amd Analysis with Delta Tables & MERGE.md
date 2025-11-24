## Lab 09 – Self Read / Analysis with Delta Tables & MERGE

###  What is “Self Read / Analysis”?

In a real enterprise pipeline, you don’t just blindly MERGE new data into an existing table.

You first:

1. **Read the current target table** (self-read).
2. **Compare** it with the incoming data (staging/incremental).
3. **Analyze conflicts & data quality** (self-analysis).
4. Then run **MERGE INTO** with confidence.

This lab makes participants practice that pattern.

---

###  Learning Objectives

By the end of this lab, learners will be able to:

* Read an existing **Delta table** (“target”) and an **incremental/staging table**.
* Detect **conflicts** (same keys, different values).
* Identify **pure inserts vs updates** before MERGE.
* Generate a simple **data quality / impact report**.
* Apply a **MERGE INTO** based on that analysis.

---

###  Prerequisites

* Running Databricks cluster.
* Unity Catalog or Hive metastore with permissions.
* Two Delta tables (we’ll create them in the lab):

  * `training.silver.orders_clean` → main target table
  * `training.bronze.orders_incremental_stage` → staging/incoming data

If you don’t already have them, the lab will create them from scratch.

---

## Part 1 – Setup: Create Target & Staging Tables

> Trainer note: If you already have these from earlier labs, you can skip the creation section and jump to Part 2.

### Step 1.1 – Create the Target Table (orders_clean)

Create a new notebook:
`Lab_Self_Read_Analysis`

Attach your cluster.

Run:

```python
from pyspark.sql import Row

# Base "target" data
target_df = spark.createDataFrame([
    Row(order_id=1, order_date="2024-01-01", customer_id=101, country="USA",   amount=100.0),
    Row(order_id=2, order_date="2024-01-02", customer_id=102, country="India", amount=200.0),
    Row(order_id=3, order_date="2024-01-03", customer_id=103, country="UK",    amount=300.0),
    Row(order_id=4, order_date="2024-01-04", customer_id=104, country="USA",   amount=400.0)
])

target_df.write.format("delta").mode("overwrite").saveAsTable("training.silver.orders_clean")
```

Verify:

```sql
%sql
SELECT * FROM training.silver.orders_clean ORDER BY order_id;
```

---

### Step 1.2 – Create the Staging/Incremental Table

This staging data will contain:

* **One updated record** (existing order with changed amount).
* **One new record** (insert).
* **One conflicting record** (bad/negative amount – for data quality example).

Run:

```python
from pyspark.sql import Row

stage_df = spark.createDataFrame([
    # Existing order with updated amount (UPDATE scenario)
    Row(order_id=2, order_date="2024-01-02", customer_id=102, country="India", amount=250.0),

    # New order (INSERT scenario)
    Row(order_id=5, order_date="2024-01-05", customer_id=105, country="Germany", amount=500.0),

    # Suspicious/bad data (e.g., negative amount)
    Row(order_id=6, order_date="2024-01-06", customer_id=106, country="USA", amount=-999.0)
])

stage_df.write.format("delta").mode("overwrite").saveAsTable("training.bronze.orders_incremental_stage")
```

Verify:

```sql
%sql
SELECT * FROM training.bronze.orders_incremental_stage ORDER BY order_id;
```

---

## Part 2 – Self Read: Load Target & Staging into DataFrames

### Step 2.1 – Read Both Tables

In the same notebook:

```python
target_df = spark.table("training.silver.orders_clean")
stage_df  = spark.table("training.bronze.orders_incremental_stage")

print("Target (orders_clean):")
target_df.orderBy("order_id").show()

print("Staging (orders_incremental_stage):")
stage_df.orderBy("order_id").show()
```

Discuss with learners:

* Target = existing state in production.
* Stage = new arriving data (daily load / CDC / incremental).

---

## Part 3 – Analysis: Classify Inserts, Updates, and Suspicious Data

### Step 3.1 – Identify Key Column

For this scenario, use:

* **Business key / primary key** = `order_id`.

In a real system, this could be a composite key.

---

### Step 3.2 – Find UPDATE Candidates (Matched Keys)

We want to find rows where:

* `order_id` exists in both target and stage → potential UPDATE.

Run:

```python
from pyspark.sql.functions import col

update_candidates_df = (
    stage_df.alias("s")
    .join(target_df.alias("t"), on="order_id", how="inner")
)

update_candidates_df.show()
```

Ask:

* Which `order_id` appears here?
* Are these purely updates or identical rows?

---

### Step 3.3 – Detect Actual Value Differences

Sometimes `order_id` exists in target & stage but values might be same or different.
We want only **meaningful changes** (e.g., amount changed).

Run:

```python
value_diff_df = (
    update_candidates_df
    .filter(col("s.amount") != col("t.amount"))
    .select(
        col("order_id"),
        col("t.amount").alias("old_amount"),
        col("s.amount").alias("new_amount")
    )
)

value_diff_df.show()
```

Now you have a **“changes report”** for amounts.

---

### Step 3.4 – Find Pure INSERTS (New Keys Only in Stage)

We want rows in staging that don’t exist in target:

```python
insert_candidates_df = (
    stage_df.alias("s")
    .join(target_df.alias("t"), on="order_id", how="left_anti")
)

insert_candidates_df.show()
```

These are new rows that will be **INSERT**ed by MERGE.

---

### Step 3.5 – Identify Suspicious / Bad Data

Example rule: negative amounts are invalid / suspicious.

```python
bad_data_df = stage_df.filter(col("amount") < 0)
bad_data_df.show()
```

You can extend this with other basic checks:

* `order_date` in the future.
* `amount` = 0.
* `customer_id` is null.

---

### Step 3.6 – Create a Simple Impact / Quality Report

Show high-level counts:

```python
from pyspark.sql.functions import lit

total_stage         = stage_df.count()
num_updates         = value_diff_df.count()
num_inserts         = insert_candidates_df.count()
num_suspicious      = bad_data_df.count()

print("Total incoming rows in stage     :", total_stage)
print("Potential UPDATEs (value change):", num_updates)
print("Potential INSERTs               :", num_inserts)
print("Suspicious rows (bad data)     :", num_suspicious)
```

Optionally, build a small DataFrame “report”:

```python
report_rows = [
    Row(metric="total_stage_rows",         value=total_stage),
    Row(metric="update_candidates_changed", value=num_updates),
    Row(metric="insert_candidates",        value=num_inserts),
    Row(metric="suspicious_bad_data",      value=num_suspicious)
]

report_df = spark.createDataFrame(report_rows)
report_df.show()
```

> Trainer note: This is the **core of “self analysis”** – reviewing the impact of new data before applying it.

---

## Part 4 – Decide What to MERGE (Apply Business Rules)

### Step 4.1 – Exclude Suspicious Data from MERGE

Let’s define a **cleaned staging dataset** that excludes bad rows
(e.g., negative amounts):

```python
clean_stage_df = stage_df.filter(col("amount") >= 0)
clean_stage_df.write.format("delta").mode("overwrite").saveAsTable("training.bronze.orders_incremental_stage_clean")
```

Check:

```sql
%sql
SELECT * FROM training.bronze.orders_incremental_stage_clean ORDER BY order_id;
```

---

## Part 5 – MERGE INTO Using Clean Staging

### Step 5.1 – Run MERGE INTO

Now we apply the ingestion into the target, based on `order_id`.

```sql
%sql
MERGE INTO training.silver.orders_clean AS target
USING training.bronze.orders_incremental_stage_clean AS source
ON target.order_id = source.order_id
WHEN MATCHED THEN
  UPDATE SET
    target.order_date   = source.order_date,
    target.customer_id  = source.customer_id,
    target.country      = source.country,
    target.amount       = source.amount
WHEN NOT MATCHED THEN
  INSERT (order_id, order_date, customer_id, country, amount)
  VALUES (source.order_id, source.order_date, source.customer_id, source.country, source.amount);
```

---

### Step 5.2 – Verify the New State of Target

```sql
%sql
SELECT * FROM training.silver.orders_clean ORDER BY order_id;
```

Check:

* `order_id = 2` → amount updated to `250.0`.
* `order_id = 5` → new row inserted.
* `order_id = 6` → NOT present (excluded as bad data).

---

### Step 5.3 – Time Travel & History (Optional)

To complete the picture:

```sql
%sql
DESCRIBE HISTORY training.silver.orders_clean;
```

Check the latest operation is a `MERGE`.

Optionally query an older version to see pre-merge state.

---

## Part 6 – Wrap-Up & Reflection

Ask participants:

1. What did we gain by doing **Self Read / Analysis** instead of blind MERGE?

   * Understanding impact.
   * Data quality checks.
   * Ability to send reports to business / audit.
2. Where would this logic live in production?

   * A notebook called by a **Workflow**.
   * A LakeFlow transformation step.
3. How could we enhance analysis?

   * More rules (null checks, referential checks).
   * Saving the report in a **Delta “audit” table**.
   * Sending alerts/emails on anomalies.

---
