##  Lab 1 – Introduction to Data Engineering in Databricks

**Covers:** “Data Engineering in Databricks” (concept + hands-on)
**Estimated Time:** 45–60 minutes

###  Learning Objectives

By the end of this lab, learners will:

* Understand what a **cluster** and **notebook** are.
* Run basic **PySpark** and **SQL** code.
* See how data engineering = **ingestion → transform → write** in Databricks.

###  Prerequisites

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
