
# ⭐ **Lab 05 — Introduction to Data Engineering in Databricks & Lakeflow Declarative Pipelines**

---

# 🧪 **Lab 1.1 – What Are Lakeflow Declarative Pipelines? (Hands-On Introduction)**

### 🎯 Learning Objectives

By the end of this lab, learners will understand:

* What **Lakeflow Declarative Pipelines** are.
* The difference between **imperative** (notebook-based) and **declarative** (YAML-based) ETL.
* How Lakeflow manages orchestration, dependencies, schema, and data quality declaratively.

---

### Step 1 — Concept (Trainer Explains)

Explain that:

### ✔ Imperative ETL (old way)

* You write Spark code manually.
* You manage schemas, merges, ingestion, errors manually.
* Pipelines are notebooks or jobs.

### ✔ Declarative ETL (Lakeflow Pipelines)

* You define **WHAT**, not **HOW**.
* You create YAML-based definitions.
* Databricks manages:

  * Ingestion
  * Schema evolution
  * Table creation
  * Data quality
  * Streaming AND batch
  * Incremental processing
  * Error handling

---

### Step 2 — Inspect a Sample Declarative Pipeline YAML

Show this example YAML (you will create your own later):

```yaml
pipeline_type: delta_live_tables

datasets:
  bronze_orders:
    type: dataset
    format: cloud_files
    path: "dbfs:/FileStore/raw/orders"
    schema: auto
    options:
      cloudFiles.inferColumnTypes: true

  silver_orders:
    type: live_table
    source: bronze_orders
    transformation:
      select: "*"
      where: "amount > 0"
```

Explain the key concepts:

* **pipeline_type**
* **datasets**
* **sources**
* **live tables**
* **transformations**

---

### Step 3 — Open Lakeflow Pipelines

1. In left sidebar → Click **Lakeflow**
2. Choose **Pipelines**
3. Click **Create Pipeline**

Expected screen: (add screenshot placeholder here)

---

### Step 4 — Create Your First Pipeline Folder

1. In Workspace → Create folder:

   * `lakeflow_course/pipelines/intro_pipeline`
2. Inside folder → Create a new file named:

   * `pipeline.yaml`

---

### Step 5 — Copy This Simple YAML

```yaml
pipeline_type: delta_live_tables

datasets:
  hello_world:
    type: live_table
    transformation:
      select: "'Hello Lakeflow' AS message"
```

---

### Step 6 — Deploy and Run the Pipeline

1. In Lakeflow Pipelines screen, choose **Add YAML File** and point to `pipeline.yaml`.
2. Name the pipeline:
   `lf_intro_pipeline`
3. Click **Start**

---

### Step 7 — Validate Output Table

Run this in a notebook:

```sql
SELECT * FROM live.hello_world;
```

---

# 🧪 **Lab 1.2 – Course Setup & Creating a Pipeline**

### 🎯 Learning Objectives:

* Set up folder structure for the entire course.
* Create your first real Lakeflow Declarative Pipeline.
* Understand the Course Project.

---

### Step 1 — Create Course Folder Structure

In Databricks Workspace, create:

```
/Users/<your_name>/lakeflow_course/
    /data/
    /pipelines/
    /src/
```

---

### Step 2 — Upload Datasets

Upload the following sample datasets into:

* `dbfs:/FileStore/lakeflow/data/orders/`
* `dbfs:/FileStore/lakeflow/data/customers/`

You can use simple CSV files such as:

**orders.csv**

```
order_id,order_date,customer_id,amount
1,2024-01-01,100,199.99
2,2024-01-02,101,299.99
...
```

**customers.csv**

```
customer_id,name,country
100,Alice,USA
101,Bob,India
...
```

---

### Step 3 — Create First Bronze Pipeline YAML

Create file:

`/lakeflow_course/pipelines/bronze_orders.yaml`

Paste this:

```yaml
pipeline_type: delta_live_tables

datasets:
  orders_bronze:
    type: dataset
    format: cloud_files
    path: "dbfs:/FileStore/lakeflow/data/orders"
    schema: auto
    options:
      cloudFiles.inferColumnTypes: true
```

---

### Step 4 — Deploy Pipeline

1. Go to **Lakeflow → Pipelines → Create**
2. Add file `bronze_orders.yaml`
3. Name pipeline: `bronze_orders_pipeline`
4. Select target catalog:

   * e.g., training
5. Click **Start**

---

### Step 5 — Validate Bronze Table

```sql
SELECT * FROM live.orders_bronze;
```

---

### Step 6 — Course Project Overview (Trainer Explains)

The complete course project:

#### 🌟 Build a full declarative Lakeflow pipeline including:

1. **Bronze ingestion**

   * orders
   * customers
2. **Silver transformations**

   * cleansing
   * joins
   * deduplication
3. **Gold aggregations**

   * revenue by country
   * revenue by month
4. **CDC ingestion using CHANGE INTO**
5. **Deploying the pipeline to production**

---
