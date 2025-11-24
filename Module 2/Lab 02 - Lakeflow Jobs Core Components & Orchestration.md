##  Lab 2 – Lakeflow Jobs Core Components & Orchestration

###  Learning Objectives

Learners will:

* Understand the **building blocks** of Lakeflow Jobs:

  * Job → Tasks → Dependencies → Clusters → Parameters.
* Create a **multi-task job** with orchestration:

  * Bronze load → Silver transform → Validation.

###  Prerequisites

* Lab 1 completed (or at least know how to create a job).
* Ability to create 2–3 simple notebooks.

---

### Step 1 – Create Three Simple Notebooks

We’ll simulate a **3-step pipeline**:

1. **Notebook 1 – Bronze Ingestion**

   Name: `lf_bronze_ingest`

   ```python
   from pyspark.sql import Row

   print("Step 1 – Bronze ingestion")

   bronze_df = spark.createDataFrame([
       Row(order_id=1, amount=100.0),
       Row(order_id=2, amount=200.0),
       Row(order_id=3, amount=300.0),
   ])

   bronze_df.write.format("delta").mode("overwrite").saveAsTable("training.bronze.orders_lf")
   print("Written table: training.bronze.orders_lf")
   ```

2. **Notebook 2 – Silver Transform**

   Name: `lf_silver_transform`

   ```python
   from pyspark.sql.functions import col

   print("Step 2 – Silver transform")

   bronze_df = spark.table("training.bronze.orders_lf")

   silver_df = bronze_df.withColumn("amount_with_tax", col("amount") * 1.18)

   silver_df.write.format("delta").mode("overwrite").saveAsTable("training.silver.orders_lf_clean")
   print("Written table: training.silver.orders_lf_clean")
   ```

3. **Notebook 3 – Validation**

   Name: `lf_validation`

   ```python
   print("Step 3 – Validation")

   df = spark.table("training.silver.orders_lf_clean")
   count = df.count()

   print("Row count in silver:", count)

   if count < 3:
       raise Exception("Validation failed: expected at least 3 rows in silver table!")
   else:
       print("Validation passed ✅")
   ```

Run each notebook once manually to confirm they work.

---

### Step 2 – Create a New Orchestrated Job

1. Go to **Lakeflow → Jobs → Create job**.
2. Name: `lf_job_etl_pipeline`.

---

### Step 3 – Add Tasks (Building Blocks)

1. **Task 1 – Bronze Ingestion**

   * Task name: `bronze_ingest`.
   * Type: **Notebook**.
   * Notebook: `lf_bronze_ingest`.
   * Compute: choose a cluster.

2. **Task 2 – Silver Transform**

   * Task name: `silver_transform`.
   * Type: **Notebook**.
   * Notebook: `lf_silver_transform`.
   * Set **Depends on**: `bronze_ingest`.

3. **Task 3 – Validation**

   * Task name: `validation`.
   * Type: **Notebook**.
   * Notebook: `lf_validation`.
   * Set **Depends on**: `silver_transform`.

You should see a **linear DAG**:

`bronze_ingest → silver_transform → validation`

---

### Step 4 – Understand Task Orchestration

Let learners visually see:

* Each box = **task**.
* Arrows = **dependency**.
* Lakeflow ensures:

  * `silver_transform` runs **only if** `bronze_ingest` succeeded.
  * `validation` runs after `silver_transform`.

---

### Step 5 – Run the Orchestrated Job

1. Click **Run now**.
2. Go to the run details:

   * Observe task-level statuses.
3. Click each task:

   * View **Output** (logs, prints).
4. Confirm:

   * All 3 tasks succeeded.
   * Table `training.silver.orders_lf_clean` exists.

---

### Step 6 – Break Something On Purpose (Optional)

To show orchestration behavior:

1. Edit `lf_validation` notebook to force a failure:

   ```python
   raise Exception("Forcing a validation error to see job behavior")
   ```

2. Run the job again.

3. Discuss:

   * Bronze and Silver might still succeed.
   * **Job status** overall = Failed.
   * How would this be handled in production?

---

### Key Takeaways

* **Building blocks** = tasks, dependencies, compute.
* Orchestration ensures **order, isolation, and reliable pipelines**.

---
