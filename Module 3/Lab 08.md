
#  **Lab: Ingest Data From SQL Server into Databricks & Detect Changes (CDC Style)**

**Difficulty:** Beginner → Intermediate
**Tools:** Databricks Notebook, SQL Server (local or Azure SQL), JDBC, Delta Lake

---

#  **Lab Overview**

You will perform:

1. **Connect Databricks to SQL Server**
2. **Ingest full data into a Bronze Delta table**
3. **Ingest incremental changes using watermarking**
4. **Automatically load change data into Silver table**
5. **Verify updates, inserts, and deletes**

---

#  **Prerequisites**

● SQL Server (local / Docker / Azure SQL)
● Database name: `SalesDB`
● Table: `Orders`
● Databricks workspace with cluster running
● Your SQL Server connection details

---

#  **Dataset Example (SQL Server Table)**

Run in SQL Server:

```sql
CREATE TABLE Orders (
    OrderID INT PRIMARY KEY,
    CustomerName VARCHAR(100),
    OrderAmount DECIMAL(10,2),
    OrderDate DATETIME DEFAULT GETDATE(),
    LastUpdated DATETIME DEFAULT GETDATE()
);

INSERT INTO Orders VALUES
(1, 'John Doe', 250.00, GETDATE(), GETDATE()),
(2, 'Alice Smith', 400.00, GETDATE(), GETDATE()),
(3, 'Bob Miller', 180.00, GETDATE(), GETDATE());
```

---

#  **Step 1 — Create SQL Server Connection Variables**

In Databricks Notebook (Python cell):

```python
sql_server_hostname = "your_sql_server_host"     # ex: 52.178.22.10 or myserver.database.windows.net
sql_server_port = "1433"
sql_server_database = "SalesDB"
sql_server_username = "youruser"
sql_server_password = "yourpassword"

table_name = "Orders"
jdbc_url = f"jdbc:sqlserver://{sql_server_hostname}:{sql_server_port};databaseName={sql_server_database}"
```

---

#  **Step 2 — Install SQL Server JDBC Driver**

Run:

```python
%pip install pyodbc
```

Attach the SQL Server driver:

```
com.microsoft.sqlserver:mssql-jdbc:12.2.0.jre11
```

(Cluster → Libraries → Install New → Maven)

---

#  **Step 3 — Full Ingestion Into Bronze Table**

```python
df_full = (spark.read
    .format("jdbc")
    .option("url", jdbc_url)
    .option("dbtable", table_name)
    .option("user", sql_server_username)
    .option("password", sql_server_password)
    .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver")
    .load()
)

df_full.display()
```

### Save to Bronze Delta Table:

```python
df_full.write.mode("overwrite").format("delta").saveAsTable("sales.bronze_orders")
```

---

#  **Step 4 — Add New and Updated Records in SQL Server**

Run in SQL Server:

```sql
UPDATE Orders
SET OrderAmount = 500.00, LastUpdated = GETDATE()
WHERE OrderID = 2;

INSERT INTO Orders VALUES 
(4, 'Diana Prince', 150.00, GETDATE(), GETDATE());
```

This simulates **changes**.

---

#  **Step 5 — Set Up Incremental CDC Using Watermark Column**

We use **LastUpdated** column as the CDC watermark.

### 5.1 — Get Last Loaded Timestamp From Bronze

```python
from pyspark.sql.functions import max

last_watermark = spark.table("sales.bronze_orders") \
    .select(max("LastUpdated")).collect()[0][0]

print("Last Loaded Timestamp:", last_watermark)
```

---

#  **Step 6 — Read Only Changed Records From SQL Server**

```python
incremental_query = f"(SELECT * FROM Orders WHERE LastUpdated > '{last_watermark}') AS t"

df_incremental = (spark.read
    .format("jdbc")
    .option("url", jdbc_url)
    .option("dbtable", incremental_query)
    .option("user", sql_server_username)
    .option("password", sql_server_password)
    .option("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver")
    .load()
)

df_incremental.display()
```

This will show:

✔ Updated Record (Order 2)
✔ Newly Inserted Record (Order 4)

---

#  **Step 7 — Append Incremental Data Into Bronze Table**

```python
df_incremental.write.mode("append").format("delta").saveAsTable("sales.bronze_orders")
```

---

#  **Step 8 — Create Silver Table With UPSERT Logic (MERGE)**

Silver table = Clean + merged + deduped.

### 8.1 Create Silver Table (first time)

```sql
CREATE TABLE IF NOT EXISTS sales.silver_orders AS
SELECT * FROM sales.bronze_orders;
```

---

### 8.2 Create MERGE Logic for Updates + Inserts

```python
from delta.tables import DeltaTable

bronze = DeltaTable.forName(spark, "sales.bronze_orders")
silver = DeltaTable.forName(spark, "sales.silver_orders")

silver.alias("s").merge(
    bronze.alias("b"),
    "s.OrderID = b.OrderID"
).whenMatchedUpdateAll(
).whenNotMatchedInsertAll(
).execute()
```

---

#  **Step 9 — Validate the Changes**

```python
spark.table("sales.silver_orders").orderBy("OrderID").display()
```

You should now see:

| OrderID | CustomerName | OrderAmount | LastUpdated       |
| ------- | ------------ | ----------- | ----------------- |
| 1       | John Doe     | 250.00      | old date          |
| 2       | Alice Smith  | **500.00**  | **new timestamp** |
| 3       | Bob Miller   | 180.00      | old               |
| 4       | Diana Prince | **150.00**  | new               |

✔ Updated
✔ Inserted
✔ Incrementally loaded

---

#  **Step 10 — Automate Using a Job (Optional)**

You can create a Databricks Job that:

1. Fetches watermark
2. Reads only changed rows
3. Appends Bronze
4. Runs MERGE to Silver
5. Sends notification

This gives you a **CDC pipeline without Log-based CDC**.

---

#  **What You Achieved**

You successfully built:

✔ SQL Server → Databricks Connection
✔ Full load ingestion
✔ Incremental load using watermark
✔ CDC simulation
✔ MERGE into Silver Delta
✔ Verified changes end-to-end

---

