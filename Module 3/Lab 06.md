#  **LAB 10 — Aggregations with Real-Time Streaming Tables**

**Duration:** 30 minutes
**Level:** Intermediate → Advanced

---

#  **Business Scenario**

The ACADO Retail analytics team needs **real-time revenue dashboards**.
Your Silver table (`training.silver.orders_clean`) receives live orders from your ingestion pipelines.

You must build a **streaming aggregate table** that continuously updates:

* Total daily revenue
* With automatic refresh
* Using Spark's streaming `window()` function
* Backed by Delta Streaming Tables

Then you will **simulate real-time order ingestion** and watch the aggregation update automatically.

---

#  PART 1 — Understand the Source Table

Before building aggregations, inspect your Silver table:

```sql
SELECT * FROM training.silver.orders_clean LIMIT 10;
```

Ensure columns:

* `order_id`
* `order_time` or `order_date`
* `customer_id`
* `amount`
* `country`

⚠ If your column is `order_date` and not `order_time`, adjust the window accordingly.

---

#  PART 2 — Build a Real-Time Streaming Aggregation Table

Databricks Streaming Tables allow **incremental SQL aggregations** using `STREAM()`.

Create a new Streaming Table:

```sql
CREATE OR REFRESH STREAMING TABLE training.stream.revenue_stream
AS
SELECT
  window(order_time, "1 day").start AS order_date,
  SUM(amount) AS total_revenue
FROM STREAM(training.silver.orders_clean)
GROUP BY 1;
```

### ✔ What this does

* `STREAM()` → ingest Silver table incrementally
* `window()` → tumbling 1-day windows
* SON increments table as new orders arrive
* Automatically checkpointed and maintained
* No cluster needed; works on serverless

---

#  PART 3 — Verify Streaming Aggregation Table

```sql
SELECT * 
FROM training.stream.revenue_stream 
ORDER BY order_date DESC;
```

Expected:

| order_date | total_revenue |
| ---------- | ------------- |
| 2024-02-10 | 25310.45      |
| 2024-02-11 | 26500.20      |

---

#  PART 4 — Simulate Real-Time Order Insertion

We will simulate a **new batch of orders** by writing new data into your Bronze table, which flows to:

Bronze → Silver → Streaming Table → Revenue Stream

### Step 4.1 — Create a Sample CSV

Upload a small CSV file with new orders:

```
order_id,order_time,customer_id,country,amount
9001,2024-02-12T10:30:00Z,101,USA,140
9002,2024-02-12T11:00:00Z,102,India,220
9003,2024-02-12T11:15:00Z,103,UK,350
```

Place into:

```
/Volumes/workspace/lab/raw/orders/
```

Or manually write using Python:

```python
import pandas as pd

new_orders = pd.DataFrame([
    (9001, "2024-02-12T10:30:00Z", 101, "USA", 140),
    (9002, "2024-02-12T11:00:00Z", 102, "India", 220),
    (9003, "2024-02-12T11:15:00Z", 103,  "UK", 350)
], columns=["order_id", "order_time", "customer_id", "country", "amount"])

spark_df = spark.createDataFrame(new_orders)

spark_df.write.format("delta") \
    .mode("append") \
    .saveAsTable("training.bronze.orders_raw")
```

---

#  PART 5 — Refresh Silver Table (If Using DLT)

If your silver layer is DLT-managed, re-run the DLT pipeline.

If your silver table is batch/streaming:

```sql
REFRESH STREAMING TABLE training.silver.orders_clean;
```

---

#  PART 6 — Watch Aggregation Update Automatically

Run:

```sql
SELECT * 
FROM training.stream.revenue_stream
ORDER BY order_date DESC;
```

Expected:

A new row appears:

| order_date | total_revenue             |
| ---------- | ------------------------- |
| 2024-02-12 | 140 + 220 + 350 = **710** |

Or, if the date exists, the sum **increases**.

---

#  PART 7 — Validate with Row Count

```sql
SELECT 
  order_date,
  total_revenue
FROM training.stream.revenue_stream
WHERE order_date = date("2024-02-12");
```

---

#  PART 8 — (Optional) Add Aggregations by Country

You can extend to:

```sql
CREATE OR REFRESH STREAMING TABLE training.stream.revenue_by_country AS
SELECT
  country,
  window(order_time, "1 day").start AS order_date,
  SUM(amount) AS revenue
FROM STREAM(training.silver.orders_clean)
GROUP BY country, order_date;
```

---

#  **LAB 10 COMPLETED — What You Learned**

You now understand:

✔ How to build a **Streaming Aggregation Table**
✔ How `STREAM()` works with Silver tables
✔ How tumbling windows calculate daily revenue
✔ How Bronze → Silver → Streaming Table propagates updates
✔ How incremental ingestion updates aggregates automatically
✔ How to simulate real-time streaming data

This is exactly how real-time revenue dashboards, fraud engines, and supply chain aggregators are built on Databricks.

---
