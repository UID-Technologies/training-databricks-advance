# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 9 & 10 – DLT SCD Type 2 + Streaming Aggregations
# MAGIC
# MAGIC This file is intended to be used as a DLT pipeline (Python).

import dlt
from pyspark.sql.functions import *

# COMMAND ----------

@dlt.table(
    name="customers_bronze",
    comment="Raw customer CDC feed from Volume"
)
def customers_bronze():
    return (
        spark.readStream
            .format("cloud_files")
            .option("cloudFiles.format", "csv")
            .load("/Volumes/workspace/lab/raw/customers_cdc")
    )

# COMMAND ----------

@dlt.table(
    name="customers_silver",
    comment="Cleaned customers table"
)
def customers_silver():
    df = dlt.read_stream("customers_bronze")
    return df.dropna(subset=["customer_id", "email"])

# COMMAND ----------

@dlt.table(
    name="customers_scd2",
    comment="SCD Type 2 dimension for customers"
)
def customers_scd2():
    return dlt.apply_changes(
        target="customers_scd2",
        source="customers_bronze",
        keys=["customer_id"],
        sequence_by=col("update_ts"),
        stored_as_scd_type="2"
    )

# COMMAND ----------

@dlt.table(
    name="orders_revenue_daily",
    comment="Daily revenue aggregation from streaming orders table"
)
def orders_revenue_daily():
    orders = dlt.read_stream("orders_silver")
    return (
        orders.groupBy(date_col=to_date(col("order_date")))
              .agg(sum("amount").alias("daily_revenue"))
    )
