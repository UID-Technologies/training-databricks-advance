

# 🚀 **LAB: Real-Time CDC From SQL Server to Databricks Using LakeFlow Connect**

**Duration:** 90 minutes
**Level:** Intermediate–Advanced
**Tools Used:** SQL Server, Databricks LakeFlow Connect, Auto Loader, Delta Tables, Streaming Queries

---

#  **1. Lab Overview (What You Will Build)**

You will build a **real-time ingestion pipeline** that:

1. Connects to **SQL Server** using *LakeFlow Connect Managed Connector*
2. Captures:
   ✔ Inserts
   ✔ Updates
   ✔ Deletes
3. Streams changes to **Bronze Delta (CDC format)**
4. Builds a **Silver MERGE table** with upserts
5. Visualizes real-time changes in Databricks

---

#  **Architecture Diagram (Real-Time CDC)**

---

#  **Prerequisites**

### ✔ SQL Server (Local, Azure SQL, or Docker)

Example DB: **SalesDB**
Example Table: **Orders**

### ✔ Databricks (Free Trial or Enterprise)

Runtime 14.x or 15.x ML

### ✔ LakeFlow Connect Enabled

(Free Trial supports SQL Server)

---

#  **2. Prepare SQL Server with CDC Enabled**

### Step 2.1 — Enable CDC at Database Level

Run in SQL Server Management Studio:

```sql
USE SalesDB;
EXEC sys.sp_cdc_enable_db;
```

---

### Step 2.2 — Create a Table to Track Changes

```sql
CREATE TABLE Orders (
    OrderID INT PRIMARY KEY,
    CustomerName VARCHAR(100),
    OrderAmount DECIMAL(10,2),
    Status VARCHAR(20),
    LastUpdated DATETIME DEFAULT GETDATE()
);

INSERT INTO Orders VALUES
(1, 'John Doe', 250.00, 'NEW', GETDATE()),
(2, 'Alice Smith', 400.00, 'NEW', GETDATE()),
(3, 'Bob Miller', 180.00, 'NEW', GETDATE());
```

---

### Step 2.3 — Enable CDC on the Table

```sql
EXEC sys.sp_cdc_enable_table
    @source_schema = 'dbo',
    @source_name   = 'Orders',
    @role_name     = NULL,
    @supports_net_changes = 1;
```

This creates a CDC table:

```
cdc.dbo_Orders_CT
```

---

#  **3. Create LakeFlow Connector in Databricks**

### Step 3.1 — Open LakeFlow Connect

Left Sidebar → **Ingest** → **Connectors**
Choose:

```
SQL Server (CDC)
```

---

### Step 3.2 — Enter Connection Details

| Field    | Example                                   |
| -------- | ----------------------------------------- |
| Host     | 40.122.x.x or server.database.windows.net |
| Port     | 1433                                      |
| Database | SalesDB                                   |
| Username | youruser                                  |
| Password | yourpass                                  |

Click **Test connection** → must PASS.

---

#  **4. Configure Real-Time CDC Pipeline**

### Step 4.1 — Select Source Table

Choose:

```
dbo.Orders
```

Databricks automatically detects:

✔ CDC enabled
✔ CDC table
✔ Primary Key

---

### Step 4.2 — Choose Destination

Destination Catalog/Schema:

```
Catalog: sales
Schema: bronze
```

Choose **CDC Mode**:

```
Capture INSERT, UPDATE, DELETE
```

---

### Step 4.3 — Write Format → Delta

Choose:

```
Bronze Table: sales.bronze_orders_cdc
```

---

### Step 4.4 — Set Auto Loader Triggers

```
Trigger: Continuous
Frequency: As fast as possible
```

---

### Step 4.5 — Start the Pipeline

Click **Start Ingestion**.

You now have a **real-time streaming CDC pipeline** from SQL Server → Databricks Bronze Delta.

---

#  **5. Validate CDC Data in Bronze Layer**

Open a new SQL cell:

```sql
SELECT * FROM sales.bronze_orders_cdc;
```

The table includes:

| _change_type | OrderID | CustomerName | OrderAmount | Status    |
| ------------ | ------- | ------------ | ----------- | --------- |
| insert       | 1       | John Doe     | 250.00      | NEW       |
| update       | 2       | Alice Smith  | 400.00      | UPDATED   |
| delete       | 3       | Bob Miller   | 180.00      | CANCELLED |

---

#  **6. Simulate Real-Time Updates in SQL Server**

Run:

```sql
UPDATE Orders
SET OrderAmount = 550.00, Status='UPDATED', LastUpdated = GETDATE()
WHERE OrderID = 2;

INSERT INTO Orders VALUES
(4, 'Diana Prince', 150.00, 'NEW', GETDATE());

DELETE FROM Orders WHERE OrderID = 3;
```

---

#  **7. Watch Live CDC in Databricks**

Run repeatedly:

```sql
SELECT * FROM sales.bronze_orders_cdc ORDER BY _commit_time DESC;
```

You will see:

✔ Updated row
✔ New row
✔ Delete record (soft delete event)

---

#  **8. Build a Silver Table (Upsert Final State)**

CDC Bronze = all events
Silver = latest state

### Step 8.1 — Create Silver Table

```sql
CREATE TABLE IF NOT EXISTS sales.silver_orders
(
    OrderID INT,
    CustomerName STRING,
    OrderAmount DOUBLE,
    Status STRING,
    LastUpdated TIMESTAMP
)
USING DELTA;
```

---

### Step 8.2 — Create Streaming MERGE Logic

In Python:

```python
from delta.tables import DeltaTable
from pyspark.sql.functions import *

bronze_stream = spark.readStream.table("sales.bronze_orders_cdc")

silver_table = DeltaTable.forName(spark, "sales.silver_orders")

def upsert_to_silver(df, batch_id):
    silver_table.alias("s").merge(
        df.alias("b"),
        "s.OrderID = b.OrderID"
    ).whenMatchedUpdateAll(
    ).whenNotMatchedInsertAll(
    ).execute()

(
    bronze_stream
    .writeStream
    .foreachBatch(upsert_to_silver)
    .outputMode("update")
    .start()
)
```

This is a **true real-time MERGE stream**.

---

#  **9. Validate Silver Table**

```sql
SELECT * FROM sales.silver_orders ORDER BY OrderID;
```

Expected:

| OrderID | Customer     | Amount  | Status  |
| ------- | ------------ | ------- | ------- |
| 1       | John Doe     | 250     | NEW     |
| 2       | Alice Smith  | **550** | UPDATED |
| 4       | Diana Prince | 150     | NEW     |

Order 3 is gone (DELETE processed).

---

#  **10. Optional — Build Gold Aggregates**

Example:

```sql
CREATE TABLE sales.gold_order_summary AS
SELECT Status, COUNT(*) AS OrderCount
FROM sales.silver_orders
GROUP BY Status;
```

Automatically updates in real time if:

```
trigger = "continuous"
```

---

#  **You Completed Real-Time CDC with SQL Server → Databricks!**

You built:

✔ SQL Server CDC enabled
✔ Databricks LakeFlow Connect pipeline
✔ Real-time ingest of INSERT/UPDATE/DELETE
✔ Bronze CDC table
✔ Silver upsert table
✔ Live streaming merge
✔ Real-time updates visible in UI

---

