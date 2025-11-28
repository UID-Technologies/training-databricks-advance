#  **LAB 3 — Delta Tables, Streaming Tables & Materialized Views**


**Level:** Intermediate
**Goal:** Learn the three foundational table types of Databricks Unity Catalog and how they behave in real-time ingestion.

---

#  **Business Scenario**

Acado Retail ingests incremental order data (bronze layer) from multiple sources.

You now need to:

1. Create a clean **Silver Delta Table**
2. Create a real-time **Streaming Table** that auto-consumes new Bronze records
3. Create a **Materialized View** for fast dashboard queries (daily revenue)

This lab simulates a real enterprise ingestion pipeline.

---

#  **PART 1 — Inspect the Existing Bronze Table**

Run:

```sql
SELECT * FROM training.bronze.orders_raw LIMIT 10;
```

Ensure fields like:

* order_id
* order_date
* customer_id
* country
* amount

---

#  **PART 2 — Create a Managed Delta Table (Silver Layer)**

This is a **standard Delta table** stored in Unity Catalog.

### Step 2.1 — Create table

```sql
CREATE TABLE training.silver.orders_clean AS
SELECT *
FROM training.bronze.orders_raw
WHERE amount > 0;
```

### What this does:

* Creates a **managed Delta table**
* Applies simple cleanup rule: only valid positive amounts
* Stores metadata in Unity Catalog
* Physically stores data in UC-managed storage

### Step 2.2 — Validate table

```sql
SELECT COUNT(*) FROM training.silver.orders_clean;
```

---

#  **PART 3 — Create a Streaming Table (Real-time SQL)**

Streaming Tables are **continuous ingestion tables**, powered by DLT-like streaming semantics.

They automatically:

* Consume new records
* Track checkpoints
* Maintain incremental state
* Refresh on every execution

### Step 3.1 — Create/Refresh Streaming Table

```sql
CREATE OR REFRESH STREAMING TABLE training.stream.orders_s
AS SELECT * FROM STREAM(training.bronze.orders_raw);
```

### What this does:

✔ `STREAM(...)` tells Databricks to consume the Bronze table **incrementally**
✔ Automatically manages offsets and checkpoints
✔ Compatible with LakeFlow ingestion
✔ Supports schema inference & evolution

### Step 3.2 — Validate

```sql
SELECT COUNT(*) FROM training.stream.orders_s;
```

This should match your bronze table record count initially.

---

#  **PART 4 — Test Streaming Behavior (Optional but Recommended)**

If you upload a new file into Bronze (`orders_new.csv`) OR re-run your ingestion job:

Run:

```sql
SELECT COUNT(*) FROM training.stream.orders_s;
```

You should see the **incremental count update** without rebuilding the table.

---

#  **PART 5 — Create a Materialized View (Daily Revenue)**

Materialized Views are:

* Incrementally updated
* Low-latency
* Auto-refreshed
* Great for BI dashboards

### Step 5.1 — Create MV

```sql
CREATE OR REFRESH MATERIALIZED VIEW training.gold.mv_daily_revenue AS
SELECT 
    date(order_date) AS order_date,
    SUM(amount) AS revenue
FROM STREAM(training.bronze.orders_raw)
GROUP BY 1;
```

### Notes:

* Uses `STREAM()` so MV auto-updates with changes to Bronze
* Target schema can be **silver** or **gold**
* Perfect for PowerBI/Tableau dashboards
* Automatically optimized

---

#  **PART 6 — Validate Materialized View**

### Step 6.1 — Query MV

```sql
SELECT * FROM training.gold.mv_daily_revenue ORDER BY order_date;
```

You should see:

| order_date | revenue  |
| ---------- | -------- |
| 2024-01-01 | 23450.20 |
| 2024-01-02 | 19880.55 |

### Step 6.2 — Check Refresh Metadata

```sql
DESCRIBE DETAIL training.gold.mv_daily_revenue;
```

Look for:

* **lastRefreshTime**
* **numRows**
* **sizeInBytes**

---

#  **PART 7 — Test Continuous Updates (Bronze → MV)**

Simulate new data ingestion (Bronze ingestion through your earlier labs).

After adding new rows, rerun:

```sql
SELECT * FROM training.gold.mv_daily_revenue ORDER BY order_date;
```

You should see new dates or increased sums — the MV automatically updated.

---

#  **PART 8 — Compare All Three Table Types**

Run this comparison:

---

## 8.1 — Delta Table (Static)

```sql
SELECT COUNT(*) FROM training.silver.orders_clean;
```

Should only update **if you run the CTAS again**.

---

## 8.2 — Streaming Table (Incremental)

```sql
SELECT COUNT(*) FROM training.stream.orders_s;
```

Updates automatically as Bronze grows.

---

## 8.3 — Materialized View (Aggregated + Fresh)

```sql
SELECT * FROM training.gold.mv_daily_revenue;
```

Shows **aggregated**, **auto-updated** revenue.

---

#  **LAB 6 COMPLETED — What You Learned**

You mastered:

✔ **Delta Tables** (Standard)
✔ **Streaming Tables** (Continuous ingestion)
✔ **Materialized Views** (Incremental aggregations)
✔ `STREAM()` SQL syntax
✔ Auto-refresh behaviors
✔ Difference between Static vs Streaming vs MV

Summary:

| Type                  | Purpose                     | Updates? | Use Case                   |
| --------------------- | --------------------------- | -------- | -------------------------- |
| **Delta Table**       | Static managed table        | ❌ Manual | Silver/Gold curated tables |
| **Streaming Table**   | Continuous ingestion        | ✔ Auto   | Real-time pipelines        |
| **Materialized View** | Incremental aggregated view | ✔ Auto   | Dashboards, BI, analytics  |

---

