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

