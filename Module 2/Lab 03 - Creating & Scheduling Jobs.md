
## 🧪 Lab 3 – Creating & Scheduling Jobs

### 🎯 Learning Objectives

Learners will:

* Configure **common task options**.
* Set **schedules and triggers**.
* Explore **run parameters** and **job-level settings**.

### ✅ Prerequisites

* Lab 2 job `lf_job_etl_pipeline` created.
* Permission to define **schedules**.

---

### Step 1 – Explore Task Configuration Options

Open your job `lf_job_etl_pipeline` in the Lakeflow Jobs UI.

For each task, explore:

1. **Cluster configuration**

   * Use existing interactive cluster vs job cluster.
2. **Timeout**

   * Set e.g. 10 minutes for `silver_transform`.
3. **Max retries**

   * Set “max retries = 2” for `validation`.
4. **Parameters (if supported)**

   * Add a parameter like `run_env = "dev"` to show how to read it in a notebook (optional).

> Trainer note: You can show them how to read job params via `dbutils.widgets` or `spark.conf` depending on pattern you prefer.

---

### Step 2 – Add a New "Report" Task

We’ll add a final report task that runs **only after validation**.

1. Add a new task:

   * Task name: `report`.
   * Type: Notebook.
   * Notebook name: `lf_report`.

Create notebook `lf_report`:

```python
print("Final report – pipeline summary")

silver_df = spark.table("training.silver.orders_lf_clean")
print("Sample from silver:")
silver_df.show()

print("Pipeline completed successfully – report generated.")
```

2. In dependencies:

   * `report` **depends on** `validation`.

Now the DAG:

`bronze_ingest → silver_transform → validation → report`

---

### Step 3 – Configure a Schedule (Job Scheduler)

1. In job `lf_job_etl_pipeline`, go to **Schedule** / **Triggers** section.
2. Turn on **Schedule**.
3. Example cron:

   * Every day at 1:00 AM.
   * Or UI option “Daily → 1:00 AM”.
4. Time zone:

   * Set to your desired region (e.g. `Asia/Kolkata` for you).

Explain:

* Jobs now **run automatically** at schedule time.
* Manual “Run Now” is still available.

---

### Step 4 – Demo: Run Now vs Scheduled Run

1. Click **Run now** to generate an immediate run.
2. Show the upcoming scheduled run in the UI (next run time).
3. Explain:

   * How to **pause** schedule.
   * How to manage schedule changes.

---

### Step 5 – Trigger on File Arrival (Optional if UI supports)

If your Lakeflow Jobs environment supports event-based triggers:

1. Show option to trigger job:

   * When files arrive in a specific storage path.
2. Explain conceptually how this is used for **near real-time ingestion**.

(Even if you don’t fully configure it, explain **use-case**.)

---

### Step 6 – Wrap-Up: When to Use Which Schedule?

Discuss:

* **Daily / Hourly** for batch ETL.
* **On file arrival** for incremental ingestion.
* **On demand only** for ad-hoc or test pipelines.

---

