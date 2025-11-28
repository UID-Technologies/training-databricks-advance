# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 11 & 12 – Unity Catalog & Power BI Helper Notebook
# MAGIC
# MAGIC This notebook contains helper SQL and notes used in UC + Power BI labs.

# COMMAND ----------
# MAGIC %sql
# MAGIC -- Example: Create external location (adjust URL & credential name)
# MAGIC CREATE EXTERNAL LOCATION IF NOT EXISTS ext_raw
# MAGIC URL 'abfss://raw@databricksadls.dfs.core.windows.net/'
# MAGIC WITH (STORAGE CREDENTIAL my_cred);

# COMMAND ----------
# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS training_ext.bronze;

# COMMAND ----------
# MAGIC %sql
# MAGIC CREATE TABLE IF NOT EXISTS training_ext.bronze.orders
# MAGIC LOCATION 'abfss://raw@databricksadls.dfs.core.windows.net/orders/'
# MAGIC AS
# MAGIC SELECT * FROM training.bronze.orders_raw;

# COMMAND ----------
# MAGIC %md
# MAGIC ## Power BI Notes
# MAGIC - Use the Databricks connector in Power BI Desktop.
# MAGIC - Connect to your SQL Warehouse endpoint.
# MAGIC - Import tables like `training.gold.daily_revenue` for reporting.
