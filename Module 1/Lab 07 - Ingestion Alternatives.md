
## Lab 07 – Ingestion Alternatives

We focus on:

* Ingesting into **existing Delta tables**.
* Using **MERGE INTO** as an ingestion strategy (self-read / self-analysis).

---

### Lab 7.1 – Ingesting into Existing Delta Tables

**Subtopics:**

* *Additional Ingestion Features Overview*
* *Ingesting into Existing Delta Tables*

**Duration:** 45–60 minutes

#### Learning Objectives

* Map incoming data to an **existing Delta table** schema.
* Handle scenarios where table already exists and you want to **append** or **merge**.
* Understand schema mapping options.

#### Prerequisites

* An existing Delta table, e.g.:
  `training.silver.orders_clean` (created in earlier labs).
* A new data source file that follows same schema (or superset).

---

#### Step 1 – Inspect Existing Delta Table

In a notebook:

```sql
%sql
DESCRIBE TABLE training.silver.orders_clean;
SELECT * FROM training.silver.orders_clean LIMIT 10;
```

Note the exact column names & types.

---

#### Step 2 – Prepare New Incoming Data

Suppose you have another CSV `orders_new.csv` with similar schema and maybe **extra columns**.

Upload to cloud storage:
`/FileStore/tables/lakeflow/orders_new/`

---

#### Step 3 – Create Ingestion Pipeline Targeting Existing Table

1. LakeFlow → Connect → **Create ingestion**.
2. Source:

   * Cloud storage → new path.
   * Format: CSV.
3. Target:

   * Catalog: `training`
   * Schema: `silver`
   * Table: **choose existing table** → `orders_clean`.
4. Choose **Write mode**:

   * `Append` (for new records).

---

#### Step 4 – Schema Mapping & Handling

If the new data has extra columns (e.g. `source_system`), you have options:

* **Drop extra columns**.
* **Map them to existing columns if names differ**.
* Or allow them into a **rescued data column**.

In LakeFlow mapping UI:

* Confirm that `order_id`, `order_date`, `customer_id`, `country`, `amount` map correctly.
* Decide what to do with extra columns.

---

#### Step 5 – Run the Ingestion and Validate

1. Run pipeline.
2. In notebook, compare:

```sql
%sql
SELECT COUNT(*) FROM training.silver.orders_clean;
```

Before and after ingestion.

3. Validate a few of the newly added rows (based on date or some filter).

---

#### Step 6 – Discussion

* When would you **append into existing tables** vs **write to a staging table** then transform?
* How does this relate to **schema-on-write** vs **schema-on-read**?

---

###  Lab 7.2 – Data Ingestion with MERGE INTO (Self Read / Analysis Pattern)

**Subtopic:**

* *Data Ingestion with MERGE INTO → SELF Read / Analysis*

**Duration:** 60–90 minutes

####  Learning Objectives

* Implement ingestion using **MERGE INTO** for upsert scenarios (slowly changing data).
* Use a **staging table** (or temporary table) as source for MERGE.
* Understand **self read / analysis** pattern:

  * Read from target
  * Compare with new data
  * MERGE changes.

#### Prerequisites

* Delta table `training.silver.orders_clean`.
* Some understanding of MERGE (from previous labs).

---

#### Step 1 – Create a Staging Table for Incremental Loads

Assume new incremental CSV or enterprise DB ingestion is landed into a **staging table**:
`training.bronze.orders_incremental_stage`

For this lab you can create it manually:

```python
from pyspark.sql import Row

incremental_df = spark.createDataFrame([
    Row(order_id=101, order_date="2024-02-01", customer_id=2001, country="USA", amount=500.00),
    Row(order_id=2,   order_date="2024-01-02", customer_id=1002, country="India", amount=150.00)  # changed amount
])

incremental_df.write.format("delta").mode("overwrite").saveAsTable("training.bronze.orders_incremental_stage")
```

---

#### Step 2 – Inspect Current Target & Staging

```sql
%sql
SELECT * FROM training.silver.orders_clean WHERE order_id IN (2, 101);

SELECT * FROM training.bronze.orders_incremental_stage;
```

Observe that:

* `order_id = 2` already exists (update scenario).
* `order_id = 101` is new (insert scenario).

---

#### Step 3 – Use MERGE INTO for Upsert

In SQL:

```sql
%sql
MERGE INTO training.silver.orders_clean AS target
USING training.bronze.orders_incremental_stage AS source
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

#### Step 4 – Validate the Result

```sql
%sql
SELECT * FROM training.silver.orders_clean WHERE order_id IN (2, 101);
```

* `order_id = 2` should now have updated `amount`.
* `order_id = 101` should exist as a new row.

---