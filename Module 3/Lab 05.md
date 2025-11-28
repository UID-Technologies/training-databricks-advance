
#  **LAB 9 — Delta Live Tables Pipeline (SCD1 + SCD2 + CDC)**

**Duration:** 60–90 minutes
**Level:** Advanced

---

#  **Business Scenario**

The ACADO Retail CRM system streams daily customer updates into Azure Storage as CSV files.
You must build a **Delta Live Tables pipeline** that:

* Ingests customer files continuously
* Cleans & validates data
* Builds a **Type 1 dimension table** (overwrite on change)
* Builds a **Type 2 dimension table** (captures history)
* Uses **CDC (Change Data Capture)** via sequence timestamps
* Runs as a **Triggered Pipeline** (Batch Streaming)

This simulates a full production-grade customer dimension pipeline.

---

#  PART 1 — Prepare Customer Data Folder

Upload customer files to:

```
/Volumes/lab/customers/
```

Example sample:

```
customer_id,first_name,last_name,email,country,update_ts
1,John,Doe,john@example.com,USA,2024-01-01T10:00:00Z
1,John,D,john@example.com,USA,2024-02-10T10:00:00Z
2,Ana,Smith,ana@example.com,India,2024-01-05T11:00:00Z
2,Ana,S,ana@example.com,India,2024-03-15T09:00:00Z
```

---

#  PART 2 — Create a DLT Python Pipeline File

Create a DLT notebook or a Python file inside Workspace:

```
lab09_dlt_customers
```

Paste the full script below:

---

#  **DLT Pipeline Script (SCD1 + SCD2 + CDC)**

```python
import dlt
from pyspark.sql.functions import *

# =======================================================
# BRONZE: Streaming ingestion of raw CSV files
# =======================================================

@dlt.table(
    name="customer_bronze",
    comment="Raw ingested customer data",
)
def customer_bronze():
    return (
        spark.readStream.format("cloud_files")
            .option("cloudFiles.format", "csv")
            .option("cloudFiles.inferColumnTypes", "true")
            .option("header", True)
            .load("/Volumes/lab/customers")
            .withColumn("ingestion_ts", current_timestamp())
    )

# =======================================================
# SILVER: Clean, validated data (SCD Type 1)
# =======================================================

@dlt.table(
    name="customer_silver",
    comment="Clean customer data with SCD Type 1 behavior",
)
def customer_silver():
    df = dlt.read_stream("customer_bronze")
    return (
        df.dropna(subset=["customer_id", "email"])
          .dropDuplicates(["customer_id"])
    )

# =======================================================
# GOLD: SCD Type 2 Dimension Table (CDC)
# =======================================================

@dlt.table(
    name="customer_scd2",
    comment="SCD Type 2 historical dimension using CDC",
)
def customer_scd2():
    return dlt.apply_changes(
        target="customer_scd2",
        source="customer_bronze",
        keys=["customer_id"],
        sequence_by=col("update_ts"),
        stored_as_scd_type=2
    )
```

---

#  PART 3 — Create a Delta Live Tables Pipeline

Navigate to:

```
Workflows → Delta Live Tables → Create Pipeline
```

### Configure:

| Field            | Value                                 |
| ---------------- | ------------------------------------- |
| Pipeline Name    | `dlt_customers_pipeline`              |
| Source           | Notebook / Python file above          |
| Target (Catalog) | `training`                            |
| Schema           | `dlt_customers`                       |
| Storage Location | `/Volumes/lab/dlt_storage/customers/` |

### Advanced Options:

✔ **Photon Enabled**
✔ **Auto Optimize → ON**
✔ **Auto-compaction → ON**
✔ **Schema Evolution → Allow**

### Mode:

Choose:

```
Triggered
```

Why Triggered?

* Runs only once per trigger
* Works in Managed Trial
* Reads cloud_files in batch mode but preserves incremental semantics

---

#  PART 4 — Run Pipeline in Triggered Mode

Click:

```
Start Pipeline
```

This does:

* Reads all CSV files from `/Volumes/lab/customers`
* Writes new data into:

  * `customer_bronze`
  * `customer_silver`
  * `customer_scd2`

---

#  PART 5 — Validate Bronze Table

```sql
SELECT * 
FROM training.dlt_customers.customer_bronze;
```

Look for:

✔ Raw rows
✔ ingestion timestamp
✔ No duplicates removed yet

---

#  PART 6 — Validate Silver (SCD Type 1)

```sql
SELECT * 
FROM training.dlt_customers.customer_silver;
```

Expected behavior:

* Deduped rows
* Clean data
* Only current values remain
* Last row wins (SCD1 overwrite)

---

#  PART 7 — Validate SCD2 (Historical Dimension)

```sql
SELECT 
  customer_id,
  first_name,
  last_name,
  update_ts,
  effective_from,
  effective_to,
  is_current
FROM training.dlt_customers.customer_scd2
ORDER BY customer_id, effective_from;
```

Expected:

| customer_id | first_name | update_ts  | effective_from | effective_to | is_current |
| ----------- | ---------- | ---------- | -------------- | ------------ | ---------- |
| 1           | John Doe   | 2024-01-01 | 2024-01-01     | 2024-02-10   | false      |
| 1           | John D     | 2024-02-10 | 2024-02-10     | null         | true       |

---

#  PART 8 — Test CDC Incremental Load

Upload a new file:

```
customer_id,first_name,last_name,email,country,update_ts
1,John,Done,john@example.com,USA,2024-03-20T10:00:00Z
3,New,Customer,new@ex.com,UK,2024-03-20T10:00:00Z
```

Re-run pipeline in Triggered mode.

Now run:

```sql
SELECT * 
FROM training.dlt_customers.customer_scd2
ORDER BY customer_id, effective_from;
```

Expected:

✔ New Type 2 record for customer 1
✔ New customer 3 is added

---

#  PART 9 — Troubleshooting & Metadata View

### Check pipeline state:

```sql
DESCRIBE DETAIL training.dlt_customers.customer_scd2;
```

Look for:

* `numRows`
* `partitionColumns`
* `deltaVersion`
* `minReaderVersion`
* `lastUpdated`

### Check DLT event logs:

Navigate:

```
Pipeline → Logs → Event Logs
```

---

#  **LAB 9 COMPLETED — What You Built**

✔ **Bronze Table** (streaming ingestion from cloud_files)
✔ **Silver Table (SCD1)** (cleaned & deduped)
✔ **Gold Table (SCD2)** (change tracking + history)
✔ **CDC pipeline** using `update_ts`
✔ **Triggered DLT execution mode**
✔ **Full customer dimension pipeline**

This is a **true enterprise SCD pipeline**, widely used in CRM, ERP, and Master Data Management (MDM) solutions.

---

