# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 1 – Auto Loader with Azure Storage Volumes
# MAGIC
# MAGIC **Objective:** Ingest CSV files incrementally using Auto Loader from a Volume.

# COMMAND ----------

# Path where you uploaded files like orders.csv, orders_2024_02.csv
volume_path = "/Volumes/workspace/lab/raw/orders/"

# COMMAND ----------

df_bronze = (
    spark.readStream
        .format("cloud_files")
        .option("cloudFiles.format", "csv")
        .option("cloudFiles.inferColumnTypes", "true")
        .load(volume_path)
)

# COMMAND ----------

(
    df_bronze.writeStream
        .format("delta")
        .option("checkpointLocation", "/Volumes/workspace/lab/chk/orders_bronze")
        .trigger(availableNow=True)
        .table("training.bronze.orders_raw")
)
