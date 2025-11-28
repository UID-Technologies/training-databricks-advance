# Databricks notebook source
# MAGIC %md
# MAGIC # Labs 7 & 8 – LakeFlow Jobs, Branching & Checkpoints
# MAGIC
# MAGIC This notebook is referenced from a Job as the validation / branching step.

# COMMAND ----------

from pyspark.sql.functions import *

df = spark.read.table("training.bronze.orders_raw")

record_count = df.count()
print(f"Record count: {record_count}")

if record_count == 0:
    dbutils.notebook.exit("EMPTY")
else:
    dbutils.notebook.exit("READY")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Inspect checkpoint folder (for Lab 8)
# MAGIC
# MAGIC Make sure you have run the streaming ingestion before this.

# COMMAND ----------

chk_path = "/Volumes/workspace/lab/chk/orders_bronze"
display(dbutils.fs.ls(chk_path))
