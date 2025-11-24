## 🧪 Lab 1 – Introduction to Data Engineering in Databricks

**Covers:** “Data Engineering in Databricks” (concept + hands-on)
**Estimated Time:** 45–60 minutes

### 🎯 Learning Objectives

By the end of this lab, learners will:

* Understand what a **cluster** and **notebook** are.
* Run basic **PySpark** and **SQL** code.
* See how data engineering = **ingestion → transform → write** in Databricks.

### ✅ Prerequisites

* Databricks workspace access.
* Permission to create a **cluster** and **notebooks**.
* Any cloud (Azure/AWS/GCP) is fine.

---

### Step 1 – Log In & Understand the Home Screen

1. Open the Databricks URL provided by the trainer.
2. After login, quickly identify:

   * **Workspace** / **Catalog** icon.
   * **Compute** (for clusters).
   * **Workflows / Jobs**.
3. Explain (trainer note):
   “Notebooks are like Jupyter. Clusters are where code runs. Data Engineering = building notebooks + pipes + jobs.”

---

### Step 2 – Create a Cluster

1. Go to **Compute** → **Create Compute** (or **Create Cluster**).
2. Recommended for lab:

   * Name: `de-training-cluster`
   * Mode: **Single User** or **Standard**
   * Node type: any small default (e.g., `2X-Small`).
   * Runtime: choose a recent **DBR with SQL & Python**.
3. Click **Create**.
4. Wait until state = **Running**.

> Trainer tip: Ask them, *“What do you think happens if cluster is stopped when you run a notebook?”* – to reinforce the concept.

---

### Step 3 – Create Your First Notebook

1. Go to **Workspace** → select your user folder.
2. Click **Create** → **Notebook**.
3. Set:

   * Name: `01_Intro_Data_Engineering`
   * Language: **Python**
   * Attach to: `de-training-cluster` (created above).
4. In the first cell, paste:

```python
spark
```

5. Run the cell (Shift + Enter) – they should see a SparkSession printout.

---

### Step 4 – Run Simple PySpark Code

1. In a new cell, run:

```python
df = spark.range(1, 101)   # numbers 1 to 100
df.show(10)
```

2. Ask them:

   * What is a DataFrame?
   * What does `show(10)` do?

3. In a new cell:

```python
df.count()
```

4. In a new cell:

```python
df_filtered = df.where("id % 2 == 0")  # even numbers
df_filtered.show(10)
```

---

### Step 5 – Use SQL in the Same Notebook

1. Add a new **SQL** cell by starting with `%sql`:

```sql
%sql
SELECT COUNT(*) AS total_rows FROM range(1, 101);
```

2. Show them:

   * Same logical operation using SQL.
   * Highlight “Single Engine, Multi-language”.

---

### Step 6 – Save Results as a Table (First Simple Pipeline)

1. Convert the range DataFrame into a table:

```python
df.write.mode("overwrite").saveAsTable("lab.bronze_numbers")
```

> If Unity Catalog is enabled, you may need:
> `catalog.schema.table` → e.g. `training.bronze.numbers`.

2. Confirm via SQL:

```sql
%sql
SELECT * FROM lab.bronze_numbers LIMIT 10;
```

3. Explain:

   * This is a **mini pipeline**:

     * Generate data → write to table → query via SQL.

---

### Step 7 – Wrap-Up Discussion

Ask participants:

* How is this different from writing scripts on plain Spark clusters?
* Where do notebooks, clusters, and tables fit into “Data Engineering in Databricks”?

---

## 🧪 Lab 2 – Ingest Data with LakeFlow Connect

**Covers:** “What is Lakeflow Connect?”
**Estimated Time:** 60–75 minutes

### 🎯 Learning Objectives

* Use **LakeFlow Connect** to ingest a file from cloud storage.
* Land data into a **bronze Delta table**.
* Understand configuration of sources & targets.

### ✅ Prerequisites

* Same cluster running (or serverless).
* A small CSV file, e.g. `orders.csv` with columns like:

  * `order_id, order_date, customer_id, country, amount`
* Storage location where you can upload this CSV (DBFS or external storage).

---

### Step 1 – Prepare the Input File

**Option A – Upload to DBFS**

1. In Databricks, click **Data** → **Add Data**.
2. Upload `orders.csv` from your local machine.
3. Note the DBFS path e.g.:
   `/FileStore/tables/orders/orders.csv`

**Option B – Upload to Cloud Storage (ADLS/S3/GCS)**
(Use if you want more enterprise-realistic lab.)

1. Upload `orders.csv` to a container/bucket, e.g.:

   * `abfss://raw@youraccount.dfs.core.windows.net/orders/orders.csv`
2. Ensure participants have read access.

---

### Step 2 – Open LakeFlow Connect

1. From the left menu, go to **LakeFlow**.
2. Click on **Connect** (or **Ingestion** depending on UI label).
3. Click **Create Ingestion** or **New pipeline**.

---

### Step 3 – Configure the Source

1. **Choose Source Type:**

   * Select **Cloud Storage** or **Files**.
2. Select:

   * Connection: your ADLS/S3/DBFS connection.
   * Path: the folder where `orders.csv` is stored.
3. File format:

   * Format: `CSV`
   * Header: **True**
   * Delimiter: `,`
4. Enable **Schema Detection** if available.

---

### Step 4 – Configure the Target (Delta Table)

1. In **Target** section:

   * Choose **Delta** as the target format.

2. Define:

   * Catalog: `training` (for example)
   * Schema: `bronze`
   * Table: `orders_raw`

3. Load mode:

   * Start with **Full Load** for first run.
   * (Explain: later we can switch to incremental.)

4. Check options like:

   * **Auto-create table**: ON.
   * **Overwrite** vs **Append**: start with **Overwrite**.

---

### Step 5 – Set Dataset Properties / Schedule (Optional)

1. For a simple lab, you can:

   * Keep schedule = **Manual** / On demand.
2. If schedule is configured, set:

   * Frequency: Once per day or hourly (for demo).

---

### Step 6 – Run the Ingestion

1. Click **Start / Run** pipeline.
2. Monitor its status:

   * Check **Run details**, **logs**, **rows ingested**.
3. Once complete, note:

   * Number of rows ingested.
   * Any schema fields recognized.

---

### Step 7 – Validate the Bronze Table

1. Open a new Notebook: `02_Lakeflow_Connect_Validation`.
2. Attach to cluster.
3. Run:

```sql
%sql
SELECT * 
FROM training.bronze.orders_raw
LIMIT 20;
```

4. Answer:

   * Are all columns present?
   * Is the schema correct (types, nullability)?

5. Run a simple aggregation:

```sql
%sql
SELECT country, COUNT(*) AS total_orders, SUM(amount) AS total_amount
FROM training.bronze.orders_raw
GROUP BY country;
```

---

### Step 8 – Discuss Incremental / CDC (Conceptual)

(You can just describe; no need to fully implement.)

* If new files arrive daily in the source folder:

  * LakeFlow can ingest **only new files**.
* For CDC:

  * Connect to databases with **change tables / logs**.
  * LakeFlow can apply insert/update/delete.

---

## 🧪 Lab 3 – Delta Lake Essentials & Time Travel

**Covers:** “Delta Lake Review”
**Estimated Time:** 60–90 minutes

### 🎯 Learning Objectives

* Create **Delta tables** using PySpark and SQL.
* Understand **ACID** behavior through updates.
* Use **Time Travel** and **DESCRIBE HISTORY**.
* Try **MERGE INTO**.

### ✅ Prerequisites

* Catalog & schema available: e.g. `training.bronze`, `training.silver`.
* A cluster running.
* The `training.bronze.orders_raw` Delta table from Lab 2 (or create a similar sample).

---

### Step 1 – Create a Cleaned Silver Table from Bronze

1. Open Notebook: `03_Delta_Essentials`.
2. Load data from bronze:

```python
df_bronze = spark.table("training.bronze.orders_raw")
df_bronze.printSchema()
df_bronze.show(5)
```

3. Apply simple cleaning:

```python
from pyspark.sql.functions import col, to_date

df_silver = (
    df_bronze
    .withColumn("order_date_parsed", to_date(col("order_date"), "yyyy-MM-dd"))
    .filter(col("order_date_parsed").isNotNull())
)

df_silver.show(5)
```

4. Write out as Delta:

```python
df_silver.write \
    .format("delta") \
    .mode("overwrite") \
    .saveAsTable("training.silver.orders_clean")
```

---

### Step 2 – Inspect Delta Table Metadata

1. Use SQL:

```sql
%sql
DESCRIBE DETAIL training.silver.orders_clean;
```

2. Ask learners:

   * Where is data stored?
   * What is the format? (Should say `delta`.)

3. View history:

```sql
%sql
DESCRIBE HISTORY training.silver.orders_clean;
```

---

### Step 3 – Perform an Update (Show ACID)

1. Simulate a correction: increase all `amount` for a specific country:

```sql
%sql
UPDATE training.silver.orders_clean
SET amount = amount * 1.1
WHERE country = 'USA';
```

2. Check results:

```sql
%sql
SELECT country, SUM(amount) AS total_amount
FROM training.silver.orders_clean
GROUP BY country;
```

3. Run `DESCRIBE HISTORY` again and show:

   * There’s a new version with an `UPDATE` operation.

---

### Step 4 – Time Travel Query

1. Identify an old version number from `DESCRIBE HISTORY` (e.g. `version = 0` or `1`).
2. Use **VERSION AS OF**:

```sql
%sql
SELECT country, SUM(amount) AS total_amount
FROM training.silver.orders_clean VERSION AS OF 0
GROUP BY country;
```

3. Compare with current version:

```sql
%sql
SELECT country, SUM(amount) AS total_amount
FROM training.silver.orders_clean
GROUP BY country;
```

4. Explain:

   * Delta keeps transaction logs.
   * You can query older snapshots without restoring backup.

---

### Step 5 – MERGE INTO (Upsert)

1. Create a small “update” DataFrame inline:

```python
from pyspark.sql import Row

updates_df = spark.createDataFrame([
    Row(order_id=1, amount=999.99, country="USA"),
    Row(order_id=9999, amount=123.45, country="Canada")
])

updates_df.createOrReplaceTempView("updates_temp")
```

2. Run MERGE:

```sql
%sql
MERGE INTO training.silver.orders_clean AS t
USING updates_temp AS s
ON t.order_id = s.order_id
WHEN MATCHED THEN
  UPDATE SET
    t.amount = s.amount,
    t.country = s.country
WHEN NOT MATCHED THEN
  INSERT (order_id, amount, country)
  VALUES (s.order_id, s.amount, s.country);
```

3. Validate:

```sql
%sql
SELECT * FROM training.silver.orders_clean
WHERE order_id IN (1, 9999);
```

4. Look again at `DESCRIBE HISTORY` and note the `MERGE` operation.

---

### Step 6 – OPTIMIZE & VACUUM (Optional for this lab)

1. Run optimization (if enabled):

```sql
%sql
OPTIMIZE training.silver.orders_clean;
```

2. Explain what OPTIMIZE and ZORDER do (you’ll go deeper in a performance lab later).

---

## 🧪 Lab 4 – Exploring the Lab Environment (Workspace + UC + DBFS)

**Covers:** “Exploring the Lab Environment”
**Estimated Time:** 45–60 minutes

### 🎯 Learning Objectives

* Explore **Workspace**, **Catalog**, **DBFS**, **Compute**, and **Workflows**.
* Understand Unity Catalog’s **Catalog → Schema → Table** model.
* Learn how to inspect files and tables interactively.

### ✅ Prerequisites

* Workspace access with Unity Catalog enabled (ideal, but not mandatory).
* At least one table already created (from previous labs).

---

### Step 1 – Explore Workspace

1. Navigate to **Workspace**.
2. Show:

   * User folders.
   * Shared folders (if any).
3. Ask learners to:

   * Create a sub-folder: `de-labs`.
   * Move their notebooks (`01_`, `02_`, `03_`) into this folder.

---

### Step 2 – Explore Catalog & Tables

1. Click on **Catalog** (or **Data**).
2. Find the catalog used in earlier labs (e.g. `training`).
3. Drill down:

   * `training` → `bronze` → `orders_raw`
   * `training` → `silver` → `orders_clean`
4. Click each table and inspect:

   * Columns
   * Data Preview
   * Permissions (if visible)

---

### Step 3 – Use DBFS Utilities

1. Open a new notebook: `04_Environment_Exploration`.
2. Attach to cluster.
3. List DBFS root:

```python
dbutils.fs.ls("/")
```

4. Identify `FileStore`, `user`, etc.

5. List uploaded files:

```python
dbutils.fs.ls("/FileStore")
```

6. If `orders.csv` was uploaded, ask them to find its exact path.

---

### Step 4 – Explore Compute

1. Go to **Compute**:

   * Show list of clusters.
   * Identify:

     * State (Running/Terminated).
     * Runtime Version.
2. Click your cluster:

   * Show **Configuration** tab (worker nodes, autoscaling).
   * Show **Metrics / Monitoring** tab (if available).
3. Explain:

   * Clusters cost money—stopping them is important.
   * Jobs can use different cluster types (job clusters vs interactive).

---

### Step 5 – Simple Workflow / Job

1. Go to **Workflows / Jobs**.
2. Click **Create Job**.
3. Name: `demo_simple_job`.
4. Task:

   * Type: **Notebook**
   * Notebook: select `03_Delta_Essentials`.
   * Cluster: use existing or job cluster with default settings.
5. Save job.
6. **Run Now**.
7. After completion, inspect:

   * Run logs.
   * Task duration.
   * Status.

---

### Step 6 – Wrap-Up Discussion

Discuss:

* How all components fit together:

  * Workspace = content.
  * Catalog = data.
  * DBFS = file system.
  * Compute = execution engine.
  * Workflows = orchestration.

---

## 👉 What next?

If you want, I can:

* **Bundle these 4 labs into a PDF-style trainer guide** (with intro, objectives, screenshots placeholders), or
* **Extend same step-by-step style for the remaining modules of the 32-hour program** (Auto Loader, DLT, Workflows, Optimization, Capstone, etc.).

Tell me:

* “Make PDF-style lab manual” **or**
* “Continue labs for remaining modules (Day 2/3/4)”
