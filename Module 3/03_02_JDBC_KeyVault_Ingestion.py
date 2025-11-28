# Databricks notebook source
# MAGIC %md
# MAGIC # Lab 2 – JDBC Ingestion from SQL DB using Key Vault + Secret Scope
# MAGIC
# MAGIC **Objective:** Securely load data from SQL Server into Databricks using secrets.

# COMMAND ----------

jdbc_user = dbutils.secrets.get("kv-scope", "db-user")
jdbc_pass = dbutils.secrets.get("kv-scope", "db-pass")

jdbc_url = "jdbc:sqlserver://<server>.database.windows.net:1433;databaseName=hrdb"

# COMMAND ----------

df_emp = (spark.read
    .format("jdbc")
    .option("url", jdbc_url)
    .option("dbtable", "dbo.Employees")
    .option("user", jdbc_user)
    .option("password", jdbc_pass)
    .load()
)

df_emp.display()

# COMMAND ----------

df_emp.write.format("delta").mode("overwrite").saveAsTable("training.bronze.sql_employees")
