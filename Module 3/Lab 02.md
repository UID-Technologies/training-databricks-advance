# **LAB 2 — Enterprise Ingestion Using LakeFlow Connect (SQL Server → Bronze → Silver)**


**Workspace:** Databricks Managed Trial **supported**
**Skill Level:** Intermediate → Advanced

This lab shows how enterprise teams use **LakeFlow Connect** for:

✔ Zero-code ingestion
✔ Secure connections via Key Vault
✔ Full load + incremental (CDC/Change Tracking)
✔ Automatic schema evolution
✔ Continuous sync into Bronze → Silver

---

---

#  **Business Scenario**

You are part of the **Acado Retail Data Engineering Team**.
The HR system stores employee master data in an **Azure SQL Database**.
Your mission:

1. Use **LakeFlow Connect Managed Connector**
2. Ingest `dbo.Employees` into **Bronze**
3. Enable **Change Tracking / CDC** for incremental updates
4. Observe **continuous synchronization** into Bronze → Silver

This eliminates custom pipelines, code, and manual JDBC work.

---

---

#  **PART 1 — Create & Configure LakeFlow Managed Connector**

### Step 1.1 — Go to LakeFlow Connect

From left navigation:

```
LakeFlow → Connectors → Add connector
```

### Step 1.2 — Choose Source System

Select:

```
Azure SQL Server → Managed Connector
```

(Databricks trial supports this.)

---

#  **PART 2 — Configure Connection Details**

Fill in the following fields:

### **2.1 — Connection Information**

| Field         | Value                         |
| ------------- | ----------------------------- |
| Host          | `server.database.windows.net` |
| Port          | `1433`                        |
| Database name | `hrdb`                        |
| Schema/table  | `dbo.Employees`               |

### **2.2 — Authentication (Key Vault)**

If your trial supports Key Vault:

* Authentication method → **Azure Key Vault**
* Secret for username → `db-user`
* Secret for password → `db-pass`

If Key Vault not available in Managed Trial:
➡ You will instead see a **“Credentials”** section
Enter username and password directly once (stored securely internally).

---

#  **PART 3 — Choose Destination (Bronze Table)**

In the “Destination” section:

```
Target Catalog   → training
Target Schema    → bronze
Target Table     → sqlserver_employees
```

LakeFlow will automatically:

✔ Create the table
✔ Infer schema
✔ Write in Delta format
✔ Generate checkpoints

---

---

#  **PART 4 — Initial Full Load (Historical Data)**

Click:

```
Start connection (Full Load)
```

The connector will extract all rows from `dbo.Employees` and write them to:

```
training.bronze.sqlserver_employees
```

### Step 4.1 — Verify from SQL

Open a new SQL cell:

```sql
SELECT COUNT(*) 
FROM training.bronze.sqlserver_employees;
```

Expected:

* A non-zero record count
* All employee rows ingested successfully

You may also preview structure:

```sql
DESCRIBE TABLE training.bronze.sqlserver_employees;
```

---

---

#  **PART 5 — Enable Incremental Load (CDC/Change Tracking)**

Now make ingestion *real-time*.

### Step 5.1 — Edit Connector Settings

Go to:

```
LakeFlow → Connectors → <your connector> → Edit
```

Under **Incremental mode**, choose one of the following:

### **Option A: SQL Server Change Tracking (recommended)**

* Toggle: **Use Change Tracking**
* Required: Change Tracking enabled on source DB

### **Option B: CDC (Change Data Capture)**

* Toggle: **Use CDC**
* Notes: Requires SQL Server Enterprise or CDC-enabled DB

### **Option C: Key-based Ingestion**

(for systems without CT/CDC support)

* Key column: `EmployeeID`
* Incremental column: `LastUpdatedDate`

---

### Step 5.2 — Save and Enable Incremental Sync

Click:

```
Save → Start sync
```

From now on:

✔ Inserts, updates, & deletes flow to Bronze
✔ Table always stays up-to-date
✔ LakeFlow handles schema drift
✔ No cron jobs required
✔ No streaming jobs needed

---

---

#  **PART 6 — Simulate Source DB Update (CDC Test)**

In SQL Server, run:

```sql
UPDATE dbo.Employees
SET Salary = Salary + 5000
WHERE EmployeeID = 101;
```

Then insert a test employee:

```sql
INSERT INTO dbo.Employees(EmployeeID, FirstName, LastName, Department, HireDate, Salary)
VALUES (999, 'Test', 'User', 'IT', GETDATE(), 90000);
```

Wait ~1 minute for sync.

---

---

#  **PART 7 — Verify Incremental Load in Bronze**

Run:

```sql
SELECT *
FROM training.bronze.sqlserver_employees
WHERE EmployeeID IN (101, 999);
```

Expected:

* Employee 101 has updated Salary
* Employee 999 appears as new row

This confirms incremental ingestion is working.

---

---

#  **PART 8 — (Optional) Auto-Generate Silver Table**

LakeFlow Connect now lets you push Bronze → Silver with schema enforcement.

### Step 8.1 — Enable “Silver Sync”

In Connector settings:

```
Enable Silver table → ON
```

Set:

```
Target: training.silver.sqlserver_employees_clean
```

Silver job does:

✔ Type enforcement
✔ Deduplication
✔ Schema evolution
✔ Soft-delete handling

### Step 8.2 — Verify Silver table

```sql
SELECT * 
FROM training.silver.sqlserver_employees_clean
LIMIT 20;
```

---

---

#  **PART 9 — Monitor the Connector**

Go to:

```
LakeFlow → Connectors → <your connector> → Monitor
```

Check:

* Full load status
* Incremental sync events
* Row counts
* Error logs
* Backfill progress
* Throughput graphs

This is essential for production pipelines.

---

---

#  **LAB COMPLETED — What You Achieved**

You successfully:

✔ Created an Azure SQL Server → Databricks Managed Connector
✔ Used Key Vault or secure credentials
✔ Performed **full batch ingestion** into Bronze
✔ Switched to **incremental ingestion (CDC/Change Tracking)**
✔ Automatically synchronized new/updated records
✔ Optionally built a Silver table
✔ Verified ingestion using SQL
✔ Set up a *true enterprise-grade ingestion pipeline*

This eliminates:

❌ JDBC code
❌ ETL jobs
❌ Scheduling complexity
❌ Schema maintenance

And gives:

✔ Always-on ingestion
✔ Reliable CDC
✔ Fully managed enterprise-grade data movement

