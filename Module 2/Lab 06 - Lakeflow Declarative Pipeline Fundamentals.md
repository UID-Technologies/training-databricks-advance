
#  **Lab 06 — Lakeflow Declarative Pipeline Fundamentals**

---

#  **Lab 2.1 – Dataset Types Overview**

###  Learning Objectives

Understand all dataset types:

| Type                     | Purpose                                |
| ------------------------ | -------------------------------------- |
| **dataset**              | Raw ingestion source                   |
| **live_table**           | Managed, incrementally refreshed table |
| **materialized_view**    | On-demand view with refresh policy     |
| **streaming_live_table** | Continuous streaming table             |

---

### Step 1 — Explore Dataset Types

Create new YAML:

`dataset_types_demo.yaml`

Paste:

```yaml
pipeline_type: delta_live_tables

datasets:
  raw_orders:
    type: dataset
    format: cloud_files
    path: "dbfs:/FileStore/lakeflow/data/orders"

  bronze_orders:
    type: live_table
    source: raw_orders

  country_mv:
    type: materialized_view
    source: bronze_orders
    transformation:
      select: "country, count(*) AS cnt"
      group_by: ["country"]
```

Deploy pipeline and view:

```sql
SELECT * FROM live.country_mv;
```

---

#  **Lab 2.2 – Simplified Pipeline Development**

### Step 1 — Create a Simple Silver Pipeline

`silver_orders.yaml`

```yaml
pipeline_type: delta_live_tables

datasets:
  orders_bronze:
    type: dataset
    format: cloud_files
    path: "dbfs:/FileStore/lakeflow/data/orders"

  orders_silver:
    type: live_table
    source: orders_bronze
    transformation:
      select: "*"
      where: "amount > 0"
```

Deploy & test:

```sql
SELECT * FROM live.orders_silver;
```

---

#  **Lab 2.3 – Common Pipeline Settings**

Add settings such as:

* `pipelines.autoOptimize`
* `pipelines.recoverOnFailure`
* `expectations`

### Step 1 — Define Settings

Create:

`pipeline_settings.yaml`

```yaml
pipeline_type: delta_live_tables

settings:
  autoOptimize:
    enabled: true
  recoverOnFailure: true
  target: "training.default"

datasets:
  orders_bronze:
    type: dataset
    format: cloud_files
    path: "dbfs:/FileStore/lakeflow/data/orders"
```

Deploy pipeline and observe the UI settings.

---

# 🧪 **Lab 2.4 – Ensure Data Quality with Expectations**

### Step 1 — Add validation rules to pipeline

`orders_quality.yaml`

```yaml
pipeline_type: delta_live_tables

datasets:
  orders_bronze:
    type: dataset
    format: cloud_files
    path: "dbfs:/FileStore/lakeflow/data/orders"

  orders_silver:
    type: live_table
    source: orders_bronze
    expectations:
      valid_amount:
        expression: "amount > 0"
        action: warn
      valid_customer:
        expression: "customer_id IS NOT NULL"
        action: error
```

Deploy & test.

Run:

```sql
SELECT * FROM live.orders_silver;
```

You will see warnings or failures based on data.

---
