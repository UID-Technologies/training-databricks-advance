
# Lab 00 – Set Up Databricks Account & Test the Environment

###  Lab Objectives

By the end of this lab, the learner will:

1. Create or access a **Databricks account & workspace**.
2. Understand the **high-level UI** (Workspace, Data, Compute, Workflows).
3. **Create a cluster** (or use serverless if available).
4. Create a **notebook**.
5. Run a **simple PySpark + SQL example** to verify the environment.

---

## Part 1 – Creating / Accessing a Databricks Account

>  *Trainer note:* If your org already provides a workspace, you can **skip to Part 2** and just give learners the Databricks URL.

### Step 1.1 – Choose Your Cloud & Sign Up

Learner options:

* **Corporate / Training setup**

  * Trainer gives:

    * Databricks URL (e.g., `https://adb-xxxxxxxx.xx.azuredatabricks.net`)
    * Login method (SSO / username & password).
* **Personal trial** (if allowed):

  * Go to **databricks.com** → click **Try Databricks Free**.
  * Choose your cloud (Azure or AWS or GCP).
  * Follow the free trial / community edition signup flow.

 At the end, the learner should have:

* A Databricks **workspace URL**
* A way to log in (Microsoft/Google/SSO/email)

Have them **log in** and stay on the home screen.

---

## Part 2 – Exploring the Databricks Workspace UI

### Step 2.1 – Identify Major UI Areas

Once logged in, ask learners to locate in the left sidebar:

* **Workspace / Catalog** – for notebooks, folders, tables.
* **Compute / Clusters** – where jobs actually run.
* **Data / Catalog** – to browse databases, schemas, tables.
* **Workflows (or Jobs / Lakeflow)** – orchestration and jobs.
* **Repos** – Git integration (optional for now).

>  *Trainer tip:* Spend 2–3 minutes asking:
>
> * “Where would you store your code?” → Workspace / Repos
> * “Where is your data registered?” → Catalog / Data
> * “What actually executes Spark code?” → Compute / Clusters

---

## Part 3 – Create & Start a Cluster (or Serverless)

> If your environment uses **Serverless** SQL / All-purpose compute, you can attach notebooks directly without manually creating a cluster. But for learning, it’s valuable to see a normal cluster.

### Step 3.1 – Go to Compute

1. In the left sidebar, click **Compute**.
2. Click **Create compute** or **Create cluster** (label varies slightly).

### Step 3.2 – Configure the Cluster (Training-Friendly)

Use these “safe” settings for training:

* **Cluster name:**
  `de-training-cluster`
* **Cluster mode:**

  * *Single User* or *Standard* (depending on your org’s recommendation)
* **Databricks Runtime version:**
  Choose a recent LTS with **Scala & Python & SQL** (e.g., 13.x / 14.x, or what your org mandates).
* **Node type / size:**
  Use a **small instance** (e.g., `2X-Small` or smallest allowed).
* **Autoscaling:**

  * Optional, but can enable:

    * Min workers: 1
    * Max workers: 2

>  *Trainer note:* Emphasize:
>
> * Clusters cost money.
> * Always **terminate** when not in use (unless job/IT manages it).

### Step 3.3 – Create the Cluster

1. Click **Create**.
2. Wait until status shows **Running** (refresh if needed).

---

## Part 4 – Create Your First Notebook

### Step 4.1 – Create a Folder for the Course

1. Click **Workspace** (or “Workspace → Users → your email”).
2. In your user area:

   * Click the **…** menu → **Create → Folder**.
   * Name it: `data-engineering-labs`.

### Step 4.2 – Create a Notebook

1. Right-click your `data-engineering-labs` folder.
2. Click **Create → Notebook**.
3. Name: `Lab0_Environment_Check`.
4. Default language: **Python**.
5. At the top of the notebook, set the **attached compute** to:

   * `de-training-cluster` (your cluster).

---

## Part 5 – Run a Simple PySpark Example

Now we’ll confirm that Spark is working.

### Step 5.1 – Verify Spark Session

In the first cell, type:

```python
spark
```

Run with **Shift + Enter**.

Expected:

* A printed representation of `SparkSession`, not an error.

If you get an error like “cluster not attached”, re-attach the cluster and re-run.

---

### Step 5.2 – Create a Tiny DataFrame

Add a new cell:

```python
data = [("Alice", 34), ("Bob", 29), ("Charlie", 40)]
columns = ["name", "age"]

df = spark.createDataFrame(data, columns)
df.show()
```

Run it.

Expected output: a small 3-row table.

Discuss:

* This is a **Spark DataFrame**, distributed computation engine, not just Pandas.

---

### Step 5.3 – Do a Transformation

Add another cell:

```python
from pyspark.sql.functions import col

df_filtered = df.filter(col("age") > 30)
df_filtered.show()
```

Explain:

* Lazy evaluation (transformations vs actions).
* This is the **core of data engineering**: read → transform → write.

---

## Part 6 – Run a Simple SQL Example

We’ll show that Databricks supports **multi-language** (Python + SQL) in the same notebook.

### Step 6.1 – Register DataFrame as a Temp View

In a new cell:

```python
df.createOrReplaceTempView("people")
```

### Step 6.2 – Query with SQL

In a new cell:

```sql
%sql
SELECT name, age
FROM people
WHERE age >= 30;
```

Run it.

Expected:

* Two rows: Alice & Charlie (based on sample data).

Explain:

* `%sql` “magic” means: this cell is executed as SQL.
* Same engine, different language → great for teams.

---

## Part 7 – Write Data to a Delta Table and Read It Back

This step confirms that:

* Storage access works
* Delta Lake is functioning

### Step 7.1 – Write as a Delta Table

In a new Python cell:

```python
df.write.format("delta").mode("overwrite").saveAsTable("lab0.people_demo")
print("Table lab0.people_demo created.")
```

>  If Unity Catalog is enforced, you may need a fully qualified name like:
> `training.lab0.people_demo` (Catalog.Schema.Table)
> Use whatever catalog & schema your trainer tells you.

### Step 7.2 – Read It Back Using SQL

```sql
%sql
SELECT * FROM lab0.people_demo;
```

(Or `SELECT * FROM training.lab0.people_demo;` depending on your environment.)

Expected:

* Same three rows as original DataFrame.

---

## Part 8 – Explore DBFS (Optional but Recommended)

This shows the learner that Databricks has a file system backing the tables.

### Step 8.1 – List Root Paths

In a new Python cell:

```python
dbutils.fs.ls("/")
```

Observe directories like:

* `/FileStore`
* `/user`
* `/databricks-datasets`
* etc.

### Step 8.2 – Explore a Public Dataset (Optional)

Try:

```python
dbutils.fs.ls("/databricks-datasets")
```

Explain:

* Databricks provides sample datasets for practice.
* You’ll use them in later labs (bronze/silver/gold, Lakeflow, etc.).

---

## Part 9 – Clean Up (Good Habit)

### Step 9.1 – Stop the Cluster *(if your org wants this)*

1. Go to **Compute**.
2. Select `de-training-cluster`.
3. Click **Terminate**.

Explain:

* Clusters **can be restarted anytime** when needed.
* In production, jobs often use **job clusters** that spin up & down automatically.

---

## Lab Summary (What Students Should Be Able to Say)

By the end, a learner should confidently say:

* “I can log in to Databricks and find **Workspace, Compute, Data, Workflows**.”
* “I can **create a cluster** and understand that it runs my code.”
* “I can create a **notebook**, attach it to a cluster, and run PySpark and SQL.”
* “I can create a **Delta table** and query it back.”

---

