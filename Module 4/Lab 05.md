#  **LAB 5 — MLflow Model Registry + Model Serving**

### **Learning Objectives**

By the end of this lab, learners will:

✔ Register the embedding model into MLflow Model Registry
✔ Promote model versions (Staging → Production)
✔ Deploy the model as a REST endpoint
✔ Query the served model for embedding inference
✔ Integrate the served model into RAG workflows

---

#  **STEP 1 — Log and Register the Model**

Use the MLflow model you created in `LAB 4`.

```python
%pip install sentence-transformers
dbutils.library.restartPython()
```


```python
import mlflow
import mlflow.pyfunc
import numpy as np
from mlflow.models import infer_signature

class Embedder(mlflow.pyfunc.PythonModel):
    def load_context(self, context):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        
    def predict(self, context, inputs):
        return self.model.encode(inputs).tolist()
```

### ✔ Log the model

```python
# 1. Create example input & output for signature
example_input = ["hello world"]
example_output = np.random.rand(384).tolist()  # MiniLM-L6 gives 384-dim embeddings

signature = infer_signature(example_input, example_output)
```

```python
# 2. Log model with signature
with mlflow.start_run() as run:
    mlflow.pyfunc.log_model(
        artifact_path="embedder",
        python_model=Embedder(),
        signature=signature
    )
    
    model_uri = f"runs:/{run.info.run_id}/embedder"
```

### ✔ Register to Model Registry

```python
# 3. Register model
registered_model = mlflow.register_model(
    model_uri=model_uri,
    name="rag_embedder_model"
)
```

### **Expected Output**

A new entry will appear in:
```
Created version '1' of model 'workspace.default.rag_embedder_model'.
```

**Databricks → Models → rag_embedder_model**

---

# **STEP 2 — Promote Model to Staging or Production**


You can do this in UI, or in the notebook:

###  Promote using MLflow API:

```python
client = mlflow.tracking.MlflowClient()

client.transition_model_version_stage(
    name="rag_embedder_model",
    version=registered_model.version,
    stage="Staging"
)
```

Or promote to production:

```python
from mlflow.tracking import MlflowClient
client = MlflowClient()

client.set_registered_model_alias(
    name="rag_embedder_model",
    alias="prod",
    version=registered_model.version
)
```

---

# **STEP 3 — Enable Model Serving**

### In Databricks Workspace:

**Serving → Create Model Serving Endpoint**

Name:

```
rag_embedder_endpoint
```

Choose model:

```
rag_embedder_model (Production)
```

Click **Create Serving Endpoint**.

Wait 2–5 minutes.

---

##  Verify Endpoint is Running

UI should show:

```
Status: READY
```

---

#  **STEP 4 — Query the Served Model (REST API)**

Get your serving endpoint URL:

```
https://<workspace>/serving-endpoints/rag_embedder_endpoint/invocations
```

### Call it using Python:

```python
import requests
import json

token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
url = "https://<workspace-url>/serving-endpoints/rag_embedder_endpoint/invocations"

payload = {"inputs": ["What is Delta Lake?"]}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

resp = requests.post(url, headers=headers, data=json.dumps(payload))
resp.json()

```

---

#  Expected Output

An embedding vector:

```
{
 "predictions": [
   [0.121, -0.331, 0.556, ...]
 ]
}
```

This is your **served embedding**.
You can now embed questions *without loading any models locally*.

---


# **STEP 5 — Use Served Model in RAG Pipeline**


Replace local embedder with served version:

### 1 Function to embed via REST endpoint

```python
def embed_via_endpoint(texts):
    payload = {"inputs": texts}
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.json()["predictions"]

```

---

### 2 Use embeddings in RAG retrieval

```python
import numpy as np
import pandas as pd

# Load your prepared chunks table from LAB 4
df = spark.read.format("delta").load("/Volumes/workspace/lab/myvolume/prepared_chunks")
pdf = df.toPandas()

# Extract text chunks and embeddings
chunks = pdf["chunk"].tolist()
vectors = np.stack(pdf["embedding"].apply(lambda x: np.array(x, dtype="float32")).values)

print("Loaded chunks:", len(chunks))
print("Vectors shape:", vectors.shape)



# Query embedding
q_emb = np.array(embed_via_endpoint(["What is Delta Lake?"])[0], dtype="float32")

# Compute similarity
similarities = np.dot(vectors, q_emb)
top_idx = similarities.argsort()[-3:][::-1]

context = "\n".join(chunks[i] for i in top_idx)

context
```



---

### 4 Build prompt and send to LLM

```python


prompt = f"""
Use ONLY the context below to answer the question.

Context:
{context}

Question: What is Delta Lake?
"""

prompt
```

Use your LLM of choice (DBRX / Llama / GPT-4o):

```python

# prompt = f"""
# Use ONLY this context to answer:

# {context}

# Question: What is Delta Lake?
# """

# llm.chat(prompt)

# Example using Databricks Model Serving
# Replace with your LLM endpoint
llm_answer = my_llm.chat(prompt)
llm_answer


```

---

#  **End-to-End Serving Architecture**

```
User Question
      ↓
Embedding Model (MLflow + Model Serving)
      ↓
Vector Search (FAISS / Mosaic)
      ↓
Top Chunks
      ↓
RAG Prompt
      ↓
LLM (DBRX / Llama / OpenAI)
      ↓
Final Grounded Answer
```

This architecture supports:

- Multi-modal RAG
- Agents & tools
- Realtime inference
- Scaling to millions of queries
- Full MLOps lifecycle

---

#  **LAB 5 Completed!**

You have now:

- Logged and registered MLflow models
- Promoted models through lifecycle stages
- Deployed a serving endpoint
- Queried the model API
- Built a production-like RAG embedding service
- Integrated it into RAG retrieval

---
