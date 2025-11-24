
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
