
## Lab 06 – Enterprise Data Ingestion with LakeFlow Connect Managed Connectors

Here we assume you have **enterprise sources** like relational DB, SaaS apps (Salesforce, Dynamics, etc.).

We’ll do **one bigger lab** that shows the pattern; you can adapt the specific source.

---

###  Lab 6.1 – Ingesting Enterprise Data with LakeFlow Managed Connectors

**Subtopics:**

* *Ingesting Enterprise Data into Databricks Overview*
* *Enterprise Data Ingestion with Lakeflow Connect*

**Duration:** 60–90 minutes

####  Learning Objectives

* Configure a **managed connector** (e.g., Azure SQL DB / PostgreSQL / Salesforce).
* Ingest data from **enterprise source tables** to Delta bronze.
* Understand **full load vs incremental** (CDC / primary key-based).

####  Prerequisites

* Credentials / connection info for one enterprise source:

  * Example: Azure SQL Database with a table `sales.orders`.
* Permission to create LakeFlow connections.

---

#### Step 1 – Understand the Source

Ask learners to inspect the source (you can provide a screenshot or schema):

Example `sales.orders` table:

```text
order_id (PK)   int
order_date      datetime
customer_id     int
status          varchar(20)
amount          decimal(10,2)
last_updated    datetime
```

---

#### Step 2 – Create a Managed Connection in LakeFlow

1. Navigate to **LakeFlow → Connections / Connectors**.
2. Click **New connection**.
3. Select connector type:

   * e.g. **Azure SQL Database** / **PostgreSQL** / **Salesforce**.
4. Fill connection details:

   * Server / Host
   * Database name
   * Port
   * Username & password / key vault reference.
5. Test connection → ensure status is **Success**.
6. Save the connection as `conn_enterprise_sql` (or similar).

---

#### Step 3 – Create an Enterprise Ingestion Pipeline

1. Go to **LakeFlow → Connect → Create ingestion**.
2. Source:

   * Connection: `conn_enterprise_sql`.
   * Source type: **Table**.
   * Choose table: `sales.orders` (or equivalent).
3. Choose **Column selection**:

   * Select all columns for now.

---

#### Step 4 – Configure Full Load to Bronze

1. Target:

   * Catalog: `training`
   * Schema: `bronze`
   * Table: `orders_enterprise_raw`
2. Load type: **Full load**.
3. Additional options:

   * Metadata columns (as in Lab 2.2).
   * Optionally, rescued data column.

---

#### Step 5 – Run the Pipeline (Initial Full Load)

1. Run the ingestion once.
2. Validate:

   * Number of records ingested matches row count in `sales.orders`.
   * Data types look correct.

In notebook:

```sql
%sql
SELECT COUNT(*) AS cnt FROM training.bronze.orders_enterprise_raw;
```

---

#### Step 6 – Configure Incremental Load (If Supported)

1. Edit the pipeline.
2. Look for **Incremental load / Change data** options:

   * For SQL DB, use:

     * **High watermark column** = `last_updated`
     * Or primary key + last updated.
3. Set:

   * Incremental column: `last_updated`
   * Start from: earliest or specific timestamp.
4. Save.

---

#### Step 7 – Simulate New/Changed Data

(Conceptual if you can’t actually modify the source; if you can, even better.)

1. Insert or update a few rows in the source database:

   * New orders with `last_updated = NOW()`.
2. Re-run the pipeline.
3. Validate that only **new/updated rows** appear in Delta, not full reload.

---

#### Step 8 – Discussion

* Difference between **standard connectors (files)** and **managed connectors (DB/SaaS)**.
* When to choose:

  * Full load only.
  * Incremental (CDC / last_updated).
* Where these enterprise ingestions fit in **Bronze → Silver → Gold**.

---
