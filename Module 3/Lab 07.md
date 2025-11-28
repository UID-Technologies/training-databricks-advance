

#  **LAB 11 — Unity Catalog: External Location + Access Policies**

**Duration:** 45 minutes
**Level:** Intermediate → Advanced

---

#  **Business Scenario**

Your ACADO Retail data lake is stored in **Azure Data Lake Storage Gen2 (ADLS)**.
You must configure **secure external access** in Unity Catalog by:

1. Creating a **Storage Credential** (bind to MSI / Service Principal)
2. Creating an **External Location**
3. Creating an **External Table** pointing to raw data in ADLS
4. Applying **fine-grained permissions** so only specific roles can query
5. Verifying access controls

This is exactly how enterprises run secure data lakes with Unity Catalog.

---

#  PREREQUISITES (Admin Needed)

### ✔ Azure ADLS Storage Account with container:

```
raw@databricksadls.dfs.core.windows.net
```

### ✔ Storage Credential already configured:

```
my_cred
```

This credential must have **Storage Blob Data Contributor** on the ADLS container.

If not yet created:

```sql
CREATE STORAGE CREDENTIAL my_cred
IDENTITY 'System Assigned Managed Identity'
WITH AZURE_MANAGED_IDENTITY;
```

---

#  PART 1 — Create External Location in Unity Catalog

External Locations are UC objects that map **cloud paths → governed access**.

### Step 1.1 — Create External Location

```sql
CREATE EXTERNAL LOCATION ext_raw
URL 'abfss://raw@databricksadls.dfs.core.windows.net/'
WITH (STORAGE CREDENTIAL my_cred);
```

### ✔ What this does

| Item               | Purpose                       |
| ------------------ | ----------------------------- |
| `ext_raw`          | Name of the governed location |
| URL                | ADLS container path           |
| Storage Credential | How we authenticate to ADLS   |

### Step 1.2 — Validate the location

```sql
DESCRIBE EXTERNAL LOCATION ext_raw;
```

Expected output:

* URL = `abfss://raw@databricksadls.dfs.core.windows.net/`
* Credential = `my_cred`
* Owner = Your user or admin

---

#  PART 2 — Create External Managed Table

Now use the external location to create a table **stored in ADLS**, not in Unity Catalog storage.

### Step 2.1 — Create Schema in External Catalog

Assuming your catalog is named:

```
training_ext
```

Create schema:

```sql
CREATE SCHEMA IF NOT EXISTS training_ext.bronze;
```

Assign default location if needed:

```sql
ALTER SCHEMA training_ext.bronze
SET LOCATION 'abfss://raw@databricksadls.dfs.core.windows.net/';
```

---

### Step 2.2 — Create External Table

Write a new bronze table into ADLS external location:

```sql
CREATE TABLE training_ext.bronze.orders
LOCATION 'abfss://raw@databricksadls.dfs.core.windows.net/orders/'
AS
SELECT * FROM training.bronze.orders_raw;
```

### ✔ What this does

* Creates table metadata in Unity Catalog
* Stores physical files in ADLS under:

```
raw/orders/
```

* Data format: Delta
* Location controlled by UC permissions

### Step 2.3 — Validate external table

```sql
DESCRIBE DETAIL training_ext.bronze.orders;
```

Look for:

* `"location"` → ADLS path
* `"format"` → delta
* `"numFiles"`
* `"tableType"` → EXTERNAL

---

#  PART 3 — Assign Access Permissions

Now enforce enterprise-grade access control.

You want to:

✔ Allow analysts to **SELECT**
✔ Prevent analysts from writing or dropping tables
✔ Keep ACADO data engineers as owners

---

### Step 3.1 — Grant SELECT on the table

```sql
GRANT SELECT ON TABLE training_ext.bronze.orders TO `data_analyst`;
```

If you’re using a group:

```sql
GRANT SELECT ON TABLE training_ext.bronze.orders TO `acuniv_data_analysts`;
```

### Step 3.2 — Verify privileges

```sql
SHOW GRANTS ON TABLE training_ext.bronze.orders;
```

Expected row:

```
data_analyst   SELECT
```

---

#  PART 4 — Test Access (Analyst View)

### Step 4.1 — Login as `data_analyst` (or use sudo impersonation)

Run:

```sql
SELECT * FROM training_ext.bronze.orders LIMIT 10;
```

Should succeed.

### Step 4.2 — Attempt to modify the table (should fail)

```sql
INSERT INTO training_ext.bronze.orders VALUES (...);
```

Expected:

❌ Permission denied
(Proof that access is read-only)

---

#  PART 5 — Optional: Assign Location-Level Permissions

If the analyst needs read access to all paths:

```sql
GRANT READ_FILES ON EXTERNAL LOCATION ext_raw TO `data_analyst`;
```

---

#  PART 6 — Optional: Use External Volume Instead of Location

Modern UC supports External Volumes:

```sql
CREATE EXTERNAL VOLUME ext_raw_vol
LOCATION 'abfss://raw@databricksadls.dfs.core.windows.net/'
WITH (STORAGE CREDENTIAL my_cred);
```

Then use it:

```sql
SELECT * FROM ext_raw_vol;
```

---

#  **LAB 11 COMPLETED — What You Learned**

You now understand:

✔ How to configure governed external locations
✔ How to assign storage credentials (MSI, SPN)
✔ How to create external managed Delta tables
✔ How to control access to external data via UC
✔ How to audit grants and permissions
✔ How to validate storage policies

**This is the foundation of modern enterprise data lake security on Databricks.**

---

