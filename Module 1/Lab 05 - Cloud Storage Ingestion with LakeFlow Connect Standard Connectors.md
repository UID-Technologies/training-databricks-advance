
## Lab 05 – Cloud Storage Ingestion with LakeFlow Connect Standard Connectors

---

###  Lab 5.1 – Introduction to Data Ingestion from Cloud Storage

**Subtopic:** *Introduction to Data Ingestion from Cloud Storage*
**Duration:** 45–60 minutes

####  Learning Objectives

By the end of this lab, learners will:

* Configure a **standard cloud storage connector** in LakeFlow Connect.
* Ingest CSV files from **cloud storage** (S3 / ADLS / GCS / DBFS) into a **Delta table**.
* Understand basic **schema detection** and **bronze layer** storage.

####  Prerequisites

* Databricks workspace + LakeFlow Connect enabled.
* Access to a cloud storage location or DBFS.
* A CSV file, e.g. `orders.csv`:

```text
order_id,order_date,customer_id,country,amount
1,2024-01-01,1001,USA,120.50
2,2024-01-02,1002,India,99.99
3,2024-01-03,1003,UK,49.99
...
```

* A catalog/schema ready, e.g.: `training.bronze`.

---

#### Step 1 – Upload or Place CSV in Cloud Storage

**Option A: Using DBFS**

1. In Databricks, go to **Data → Add Data**.
2. Click **Upload File** and choose `orders.csv`.
3. Note the resulting path, e.g.:
   `/FileStore/tables/lakeflow/orders/orders.csv`

**Option B: Using ADLS/S3/GCS**

1. Upload `orders.csv` to a folder such as:

   * ADLS: `abfss://raw@youraccount.dfs.core.windows.net/orders/`
   * S3: `s3://your-bucket/raw/orders/`
2. Ensure Databricks has read permissions on this location.

---

#### Step 2 – Open LakeFlow Connect

1. In the Databricks UI, choose **LakeFlow** from the left menu.
2. Click on **Connect** (or **Ingestion**, depending on UI).
3. Click **Create ingestion** / **New ingestion pipeline**.

---

#### Step 3 – Configure Source (Cloud Storage)

1. In **Source type**, select:

   * **Cloud storage** or **File storage** (whichever terminology is present).

2. Select or create an appropriate **connection**:

   * Choose your ADLS/S3/DBFS connection.

3. Set the **Source Path**:

   * Folder where `orders.csv` resides (e.g. `/FileStore/tables/lakeflow/orders/`).

4. File format:

   * Format: `CSV`
   * Header: **Yes**
   * Delimiter: `,`
   * Encoding: UTF-8 (default).

5. Turn on **Auto-detect schema** if available.

---

#### Step 4 – Configure Target (Delta Table in Bronze Layer)

1. In **Target configuration**, select **Delta** as output format.
2. Target location:

   * Catalog: `training`
   * Schema: `bronze`
   * Table name: `orders_raw_cloud`
3. Load strategy:

   * Initial load: **Overwrite** (safe for lab).
   * Check **Auto-create table**.

---

#### Step 5 – Run the Ingestion Job

1. Review the summary page:

   * Source path
   * Target table
   * Schema preview
2. Click **Run** or **Start ingestion**.
3. Wait for the run to complete.
4. Observe:

   * Number of files read.
   * Number of records ingested.
   * Any warnings/errors.

---

#### Step 6 – Validate the Ingested Data (SQL)

1. Open a Notebook named: `Lab_2_1_Cloud_Ingestion_Validation`.
2. Attach to your cluster.
3. Run:

```sql
%sql
SELECT * 
FROM training.bronze.orders_raw_cloud
LIMIT 20;
```

4. Basic sanity checks:

   * Column names match the CSV header.
   * Row counts match expected number in CSV.
   * Data types look reasonable (numeric vs string).

---

#### Step 7 – Discussion

* Ask learners:

  * What happens if a new CSV file is dropped in the same folder?
  * How would you configure incremental ingestion next?

---

---

###  Lab 5.2 – Appending Metadata Columns on Ingest

**Subtopic:** *Appending Metadata Columns on Ingest*
**Duration:** 30–45 minutes

####  Learning Objectives

* Configure LakeFlow Connect to automatically add **metadata columns**:

  * Ingestion timestamp
  * Source file path
  * Batch ID, etc.
* Understand why metadata is important for **auditing** and **troubleshooting**.

####  Prerequisites

* Lab 5.1 completed.
* Another CSV file or the same folder with multiple files, such as `orders_2024_01.csv`, `orders_2024_02.csv`.

---

#### Step 1 – Prepare Multiple Source Files

1. Add another CSV file in the same folder:

   * `orders_2024_02.csv` with similar schema.
2. Confirm both files exist in cloud storage.

---

#### Step 2 – Create a New LakeFlow Ingestion with Metadata

1. Go to **LakeFlow → Connect**.
2. Click **Create ingestion**.
3. Source:

   * Same cloud storage connection.
   * Point to folder (not a single file!) where multiple `orders_*.csv` exist.
   * Format: `CSV`
4. Target:

   * Catalog: `training`
   * Schema: `bronze`
   * Table: `orders_with_metadata`

---

#### Step 3 – Configure Metadata Columns

Find section like **“Advanced options / Metadata columns / Additional columns”** (names may vary slightly).

Add the following:

* `ingest_file_path` → **Source File Path**
* `ingest_time` → **Current Timestamp**
* `ingest_batch_id` → pipeline’s **run id** or **batch id** (if available)

Exact UI names vary, but generally:

1. Click **Add metadata column**.
2. Choose:

   * Column name: `ingest_file_path`
   * Value: **File path**
3. Add:

   * Column name: `ingest_time`
   * Value: **Ingestion timestamp**
4. Optionally:

   * Column name: `ingest_batch_id`
   * Value: **Ingestion run id** / **batch id**

---

#### Step 4 – Run Ingestion

1. Run the ingestion pipeline.
2. Wait for completion.
3. Confirm:

   * Both files are processed.
   * No schema errors.

---

#### Step 5 – Validate Metadata Columns

In a notebook:

```sql
%sql
SELECT 
  order_id, order_date, customer_id, country, amount,
  ingest_file_path,
  ingest_time,
  ingest_batch_id
FROM training.bronze.orders_with_metadata
LIMIT 20;
```

Questions to ask:

* Do rows from each file have the correct `ingest_file_path`?
* Are ingestion timestamps populated?

---

#### Step 6 – Discussion

* How would these metadata columns help in:

  * Debugging wrong data?
  * Performing replays from a specific file or batch?
  * Building lineage?

---

---

###  Lab 5.3 – Working with the Rescued Data Column

**Subtopic:** *Working with the Rescued Data Column*
**Duration:** 45–60 minutes

####  Learning Objectives

* Understand what the **rescued data column** is.
* See how LakeFlow stores unparseable / extra columns in this JSON-like field.
* Learn how to analyze and fix bad data.

####  Prerequisites

* Basic ingestion pipeline working (Lab 2.1).
* Ability to edit / create “slightly bad” CSV files.

---

#### Step 1 – Create a “Dirty” CSV File

Create a file `orders_dirty.csv` with issues like:

* Extra column in some rows.
* Wrong data type in `amount`.
* Extra unexpected column header.

Example:

```text
order_id,order_date,customer_id,country,amount,extra_column
1,2024-01-01,1001,USA,120.50,OK
2,2024-01-02,1002,India,ERROR_AMOUNT,NOTE
3,2024-01-03,1003,UK,49.99,
```

Upload to the same or new folder:
`/FileStore/tables/lakeflow/orders_dirty/`

---

#### Step 2 – Create Ingestion with Rescued Data Enabled

1. Go to **LakeFlow → Connect → Create ingestion**.
2. Source:

   * Cloud storage → path to the dirty folder.
   * Format: CSV
3. In **Schema / Advanced options**:

   * Enable **Rescued data column** (may be named “Column for unexpected fields / errors”).
   * Provide a name: `_rescued_data` (or default name if enforced).
4. Target:

   * Catalog: `training`
   * Schema: `bronze`
   * Table: `orders_dirty_bronze`

---

#### Step 3 – Run Ingestion and Observe

1. Run the pipeline.
2. Once completed:

   * Note if there were **schema warnings**.
   * Check for partial records vs fully rejected records.

---

#### Step 4 – Inspect the Rescued Data Column

In a notebook:

```sql
%sql
SELECT 
  order_id,
  order_date,
  customer_id,
  country,
  amount,
  _rescued_data
FROM training.bronze.orders_dirty_bronze;
```

Look for:

* Null vs non-null `_rescued_data`.
* Types of errors captured:

  * Extra column values
  * Fields that didn’t match schema.

---

#### Step 5 – Parse Rescued Data for Analysis

Use SQL JSON functions (example; names differ slightly per runtime):

```sql
%sql
SELECT 
  order_id,
  amount,
  _rescued_data,
  get_json_object(_rescued_data, '$.extra_column') AS extra_col_value
FROM training.bronze.orders_dirty_bronze;
```

Or using PySpark:

```python
df = spark.table("training.bronze.orders_dirty_bronze")
df.select("order_id", "amount", "_rescued_data").show(truncate=False)
```

---

#### Step 6 – Discussion

* What’s better: **drop bad rows** or **rescue bad fields**?
* How can rescued data help:

  * During schema evolution?
  * During debugging of upstream producers?

---

---

###  Lab 5.4 – Ingesting Semi-Structured Data: JSON

**Subtopic:** *Ingesting Semi-Structured Data: JSON*
**Duration:** 45–60 minutes

####  Learning Objectives

* Ingest **JSON** files from cloud storage using LakeFlow standard connectors.
* Understand how nested JSON becomes **struct** / **array** columns in Delta.
* Practice flattening nested JSON into relational columns.

####  Prerequisites

* LakeFlow Connect accessible.
* Sample JSON file, e.g. `customers.json`:

```json
{"customer_id": 1, "name": "Alice", "contact": {"email": "alice@example.com", "phone": "123456"}, "tags": ["premium","newsletter"]}
{"customer_id": 2, "name": "Bob", "contact": {"email": "bob@example.com", "phone": "999999"}, "tags": ["trial"]}
```

Each line = one JSON object (**ndjson** style).

---

#### Step 1 – Upload JSON to Cloud Storage

1. Upload `customers.json` to:

   * DBFS: `/FileStore/tables/lakeflow/customers/customers.json`
     or
   * ADLS/S3: your desired folder.

---

#### Step 2 – Configure JSON Ingestion in LakeFlow

1. **LakeFlow → Connect → Create ingestion**.
2. Source:

   * Cloud storage connection.
   * Path: folder where `customers.json` is stored.
   * File format: `JSON`
   * Option: `Multiline = false` (since each line is a JSON object).
3. Target:

   * Catalog: `training`
   * Schema: `bronze`
   * Table: `customers_raw_json`
4. Enable **auto-detect schema**.

---

#### Step 3 – Run Ingestion

1. Run the ingestion.
2. Validate that it succeeds without schema errors.

---

#### Step 4 – Inspect Nested Structure

In notebook:

```python
df = spark.table("training.bronze.customers_raw_json")
df.printSchema()
df.show(truncate=False)
```

Expected schema (example):

* `customer_id` – long
* `name` – string
* `contact` – struct

  * `email` – string
  * `phone` – string
* `tags` – array<string>

---

#### Step 5 – Flatten JSON into Silver Table

Use PySpark:

```python
from pyspark.sql.functions import col, explode

df = spark.table("training.bronze.customers_raw_json")

df_flat = (
    df
    .withColumn("email", col("contact.email"))
    .withColumn("phone", col("contact.phone"))
)

df_flat.write.format("delta").mode("overwrite").saveAsTable("training.silver.customers_flat")
```

Inspect:

```sql
%sql
SELECT * FROM training.silver.customers_flat;
```

Optionally, explode tags:

```python
df_tags = df_flat.withColumn("tag", explode("tags"))
df_tags.write.format("delta").mode("overwrite").saveAsTable("training.silver.customers_tags")
```

---

#### Step 6 – Discussion

* How does JSON ingestion differ from CSV?
* Which layer is best to keep nested vs flattened form (bronze vs silver)?

---








