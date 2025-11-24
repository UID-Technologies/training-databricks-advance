#### Step 08 – Self Read / Analysis Concept

Explain / Demo the pattern:

1. **Self-Read**:

   * Read current target table (`orders_clean`) into a DataFrame.
2. Analyze where new data would conflict or cause duplicates.
3. Apply MERGE to reconcile.

Example:

```python
target_df = spark.table("training.silver.orders_clean")
stage_df = spark.table("training.bronze.orders_incremental_stage")

# Example analysis: find conflicts
conflicts_df = stage_df.join(
    target_df,
    on="order_id",
    how="inner"
)

conflicts_df.show()
```

Discuss how such pre-MERGE analysis is useful for **data quality checks**.

---

#### Step 6 – Discussion

* When do you prefer MERGE-based ingestion vs. simple APPEND?
* How does MERGE impact performance on large tables?
* How can this be orchestrated in **Workflows / LakeFlow pipelines**?

---
