##  Lab 4 – Exploring the Lab Environment (Workspace + UC + DBFS)

**Covers:** “Exploring the Lab Environment”
**Estimated Time:** 45–60 minutes

###  Learning Objectives

* Explore **Workspace**, **Catalog**, **DBFS**, **Compute**, and **Workflows**.
* Understand Unity Catalog’s **Catalog → Schema → Table** model.
* Learn how to inspect files and tables interactively.

###  Prerequisites

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
