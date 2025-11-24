
# ⭐ **Lab 07 — Building Lakeflow Declarative Pipelines (Advanced)**

---

# 🧪 **Lab 3.1 – Streaming Joins Overview**

### Step 1 — Create streaming customers and orders

YAML:

```yaml
datasets:
  streaming_orders:
    type: streaming_live_table
    source:
      type: cloud_files
      path: "dbfs:/FileStore/lakeflow/data/orders_stream"
      schema: auto

  customers_silver:
    type: live_table
    format: json
    path: "dbfs:/FileStore/lakeflow/data/customers"

  orders_enriched:
    type: live_table
    sources:
      - streaming_orders
      - customers_silver
    transformation:
      join:
        left: "streaming_orders"
        right: "customers_silver"
        on: "streaming_orders.customer_id = customers_silver.customer_id"
```

---

# 🧪 **Lab 3.2 – Deploy Pipeline to Production**

### Step 1 — Promote pipeline from dev → prod

Trainer explains:

Production uses:

* Job clusters
* Versioned YAML
* CI/CD (Git + Repos)

Steps:

1. Publish YAML to Git repository.
2. Connect Repo in Databricks.
3. Deploy pipeline from repo path.
4. Configure proper compute.
5. Add schedule (hourly/daily).
6. Add alerts.

---

# 🧪 **Lab 3.3 – Change Data Capture (CDC) Overview**

Explain that:

* Lakeflow supports CDC via **CHANGE INTO** syntax.
* Used for upserts.

---

# 🧪 **Lab 3.4 – Hands-On: CDC Using CHANGE INTO**

### Step 1 — Create CDC source dataset

Upload CDC data:

`orders_cdc.csv`:

```
order_id,amount,_change_type
1,250,update
5,500,insert
3,NULL,delete
```

### Step 2 — Create CDC Pipeline

`orders_cdc_pipeline.yaml`

```yaml
pipeline_type: delta_live_tables

datasets:
  raw_cdc:
    type: dataset
    format: cloud_files
    path: "dbfs:/FileStore/lakeflow/data/cdc"

  orders_target:
    type: live_table
    source: raw_cdc
    apply_changes_into:
      target: training.silver.orders_cdc
      keys: ["order_id"]
      sequence_by: "_ingest_time"
      except_columns: ["_change_type"]
      apply_as_deletes:
        expression: "_change_type = 'delete'"
```

Deploy & validate:

```sql
SELECT * FROM training.silver.orders_cdc;
```

---

# 🧪 **Lab 3.5 – Additional Features Overview**

Trainer quickly demonstrates:

* Pipeline snapshots
* Auto-monitoring
* Error observability
* Catalog switching
* Using `materialized_view` for gold aggregates

---

# 🎉 If you'd like next:

I can produce:

✅ A full **PDF-ready Lab Manual**
✅ A full **32-hour structured course**
✅ A **project template** for students
✅ **Slide deck** with diagrams
✅ A **Git repo folder structure** for declarative pipelines

Just tell me **“Create Lab Manual PDF packet”** or **“Create slides for this module”**.
