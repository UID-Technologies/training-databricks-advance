
#  **LAB 6 — RAG with Tools + Agents**

**Assumptions (from Lab 5):**

* You already have a serving endpoint named:
  **`rag_embedder_endpoint`**
* You already have stored chunks at:
  `/Volumes/workspace/lab/myvolume/prepared_chunks`
* You already know your LLM endpoint
  (example: `test-endpoint` – replace in notebook)


---

##  **STEP 1 — Imports & Setup**

```python
# COMMAND ----------
import requests, json, numpy as np, pandas as pd
import os
```

---

##  **STEP 2 — Setup Embedding Endpoint (from LAB 5)**

```python
# COMMAND ----------
# Reuse the embedding model from Lab 5
token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

workspace = spark.conf.get("spark.databricks.workspaceUrl")
EMBED_URL = f"https://{workspace}/serving-endpoints/rag_embedder_endpoint/invocations"

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
```

---

##  **STEP 3 — Embed Helper Using Model Serving**

```python
# COMMAND ----------
def embed(texts):
    """Embed text using the served MLflow embedding model."""
    payload = {"inputs": texts}
    resp = requests.post(EMBED_URL, headers=headers, data=json.dumps(payload))
    return resp.json()["predictions"]
```

---

##  **STEP 4 — Load Chunks (Generated in Lab 4/5)**

```python
# COMMAND ----------
df = spark.read.format("delta").load("/Volumes/workspace/lab/myvolume/prepared_chunks")
pdf = df.toPandas()

chunks = pdf["chunk"].tolist()
vectors = np.stack(pdf["embedding"].apply(lambda x: np.array(x, dtype="float32")).values)

len(chunks), vectors.shape
```

---

##  **STEP 5 — Build RAG Retriever (Using Served Embeddings)**

```python
# COMMAND ----------
def rag_search(query):
    """Return top chunks based on embedding similarity."""
    
    # embed query using serving endpoint
    q_emb = np.array(embed([query])[0], dtype="float32")
    
    sims = np.dot(vectors, q_emb)
    top_idx = sims.argsort()[-3:][::-1]
    
    top_chunks = [chunks[i] for i in top_idx]
    context = "\n\n".join(top_chunks)
    
    return {
        "context": context,
        "top_chunks": top_chunks
    }
```

---

##  **STEP 6 — Add Calculator Tool**

```python
# COMMAND ----------
def calculator(expression: str):
    allowed = "0123456789+-*/(). "
    if not all(c in allowed for c in expression):
        return "Invalid characters."
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error: {e}"
```

---

##  **STEP 7 — Optional SQL Tool**

```python
# COMMAND ----------
def sql_query(query):
    try:
        df = spark.sql(query)
        return df.limit(10).toPandas().to_json(orient="records")
    except Exception as e:
        return f"SQL Error: {e}"
```

---

##  **STEP 8 — Define Tool Schemas for the LLM**

```python
# COMMAND ----------
tools = [
    {
        "type": "function",
        "function": {
            "name": "rag_search",
            "description": "Retrieve knowledge using the RAG vector store",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Perform arithmetic computations",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string"}},
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sql_query",
            "description": "Execute SQL on Databricks",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"]
            }
        }
    }
]

# Mapping tool names → Python functions
tool_map = {
    "rag_search": rag_search,
    "calculator": calculator,
    "sql_query": sql_query
}
```

---

##  **STEP 9 — LLM Client (Databricks Foundation Models)**

```python
# COMMAND ----------
class DatabricksLLM:
    def __init__(self, endpoint):
        self.url = f"https://{workspace}/serving-endpoints/{endpoint}/invocations"
        self.token = token

    def chat(self, messages, tools=None):
        payload = {"messages": messages}
        if tools:
            payload["tools"] = tools
        
        response = requests.post(
            self.url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            },
            data=json.dumps(payload)
        )
        return response.json()
```

---

### Select your LLM endpoint

```python
# COMMAND ----------
llm = DatabricksLLM("test-endpoint")   # CHANGE THIS to your LLM endpoint
```

---

##  **STEP 10 — Build the AGENT (Planner → Tool Caller → Answer)**

```python
# COMMAND ----------
def agent(query):
    # Step 1 — Ask LLM what to do
    messages = [{"role": "user", "content": query}]
    response = llm.chat(messages, tools=tools)
    
    # If no tool call → return direct answer
    if "tool_calls" not in response.get("message", {}):
        return response["message"]["content"]
    
    tool_call = response["message"]["tool_calls"][0]
    tool_name = tool_call["name"]
    args = json.loads(tool_call["arguments"])
    
    # Step 2 — Execute tool in Python
    result = tool_map[tool_name](**args)
    
    # Step 3 — Send result back to LLM
    messages.append(response["message"])
    messages.append({
        "role": "tool",
        "tool_name": tool_name,
        "content": json.dumps(result)
    })
    
    final = llm.chat(messages)
    return final["message"]["content"]
```

---

#  **STEP 11 — TEST THE AGENT**

---

##  RAG Search Test

```python
# COMMAND ----------
agent("What is Delta Lake?")
```

---

##  Calculator Test

```python
# COMMAND ----------
agent("What is 999 * 38?")
```

---

##  Multi-step Reasoning (RAG + Calculator)

```python
# COMMAND ----------
agent("Using training notes, explain MLflow and compute 36 * 14.")
```

---

##  SQL Tool Test (Optional)

```python
# COMMAND ----------
agent("Run SQL: SELECT 1 AS test_value")
```

---

#  **LAB 6 Completed Successfully!**

Your agent now supports:

- Tool calling
- RAG retrieval (served embeddings → vector search)
- Calculator
- SQL execution
- Multi-step reasoning
- Databricks Foundation Model integration

--

--------------




<!-- 

**single, self-contained Databricks notebook** for:

* RAG as a **tool**
* Calculator as a **tool**
* Optional **SQL tool**
* **Agent with function calling** using Databricks Foundation Models via the **OpenAI-compatible client** (no `from databricks import llm`, so no ImportError). ([Databricks Documentation][1])


---

```python
# Databricks notebook source
# ============================================
# LAB 6 – RAG with Tools + Agents (Compound AI)
# ============================================

# In this lab you will:
# - Build a simple in-memory RAG retriever
# - Expose RAG as a "tool"
# - Add a calculator tool (and optional SQL tool)
# - Build an Agent that uses Databricks Foundation Models (OpenAI-compatible API)
# - Use function calling / tool calling for planning + acting + reasoning
```

```python
# COMMAND ----------
# STEP 0 – Install Dependencies (if needed)

# Run once per cluster
%pip install sentence-transformers openai

dbutils.library.restartPython()
```

```python
# COMMAND ----------
# STEP 1 – Imports & LLM Client Setup

import os
import json
import numpy as np

from sentence_transformers import SentenceTransformer
from openai import OpenAI

# -----------------------------------------
# Databricks Foundation Models (OpenAI-compatible)
# -----------------------------------------
# In Databricks notebooks, DATABRICKS_HOST and DATABRICKS_TOKEN
# are usually pre-populated. If not, set them manually in cluster env vars.

DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST")
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN")

assert DATABRICKS_HOST is not None, "DATABRICKS_HOST env var is not set"
assert DATABRICKS_TOKEN is not None, "DATABRICKS_TOKEN env var is not set"

client = OpenAI(
    api_key=DATABRICKS_TOKEN,
    base_url=f"{DATABRICKS_HOST}/serving-endpoints",
)

# Use any chat-capable Foundation Model endpoint here.
# Examples (depends on what exists in YOUR workspace):
# - "databricks-llama-4-maverick"
# - "databricks-meta-llama-3-1-70b-instruct"
# - "databricks-dbrx-instruct"
FOUNDATION_MODEL_NAME = "databricks-llama-4-maverick"  # <-- adjust if needed
```

```python
# COMMAND ----------
# STEP 2 – Build a Tiny "Training Notes" Corpus for RAG

documents = [
    """
    Delta Lake is an open storage format that brings reliability to data lakes.
    It adds ACID transactions, schema enforcement, and time travel on top of Parquet files.
    In Databricks, Delta Lake powers the Lakehouse architecture and is deeply integrated
    with Spark, Unity Catalog, and Structured Streaming.
    """,
    """
    MLflow is an open-source platform for the machine learning lifecycle.
    It helps you track experiments, log models and parameters, register models,
    and deploy them via Model Serving. In Databricks, MLflow is built-in and
    tightly integrated with Unity Catalog and Mosaic AI.
    """,
    """
    Unity Catalog is the unified governance layer for Databricks.
    It provides centralized governance for data, AI assets, notebooks, and dashboards.
    It gives fine-grained access control, lineage, data discovery, and is the
    foundation for secure multi-tenant Lakehouse deployments.
    """,
    """
    Delta Live Tables (DLT) is a framework for building reliable ETL pipelines.
    It supports declarative pipeline definitions in SQL and Python, automatic
    data quality checks, and managed orchestration on Databricks.
    """,
]

len(documents)
```

```python
# COMMAND ----------
# STEP 3 – Simple Chunking + Embeddings

# Very simple paragraph-based chunking for the lab
chunks = []
for doc in documents:
    for para in doc.split("\n"):
        para = para.strip()
        if len(para) > 50:
            chunks.append(para)

print("Number of chunks:", len(chunks))
for i, c in enumerate(chunks):
    print(f"\n--- Chunk {i} ---\n{c}")
```

```python
# COMMAND ----------
# STEP 4 – Load Embedding Model & Create Vector Index (in memory)

embedder = SentenceTransformer("all-MiniLM-L6-v2")

# Encode all chunks
chunk_embeddings = embedder.encode(chunks)
vectors = np.array(chunk_embeddings)

vectors.shape
```

```python
# COMMAND ----------
# STEP 5 – Define RAG Retriever as a TOOL

def rag_tool(query: str) -> dict:
    """
    Simple in-memory RAG retriever.
    Returns top-3 chunks + concatenated context.
    """
    # Embed the query
    q_emb = embedder.encode([query])[0]

    # Cosine similarity via dot product on normalized vectors (here: plain dot for simplicity)
    sims = np.dot(vectors, q_emb)
    top_idx = sims.argsort()[-3:][::-1]

    top_chunks = [chunks[i] for i in top_idx]
    context = "\n\n".join(top_chunks)

    return {
        "context": context,
        "top_chunks": top_chunks,
    }

# Quick manual test of retriever
test_result = rag_tool("What is Delta Lake?")
test_result["context"]
```

```python
# COMMAND ----------
# STEP 6 – Define Another TOOL: Calculator

def calculator_tool(expression: str) -> str:
    """
    Very simple calculator tool.
    WARNING: eval() is not safe in real production.
    For lab/demo only.
    """
    try:
        # Only allow digits, operators and basic parentheses to avoid obvious abuse in this demo
        allowed_chars = "0123456789+-*/(). "
        if not all(ch in allowed_chars for ch in expression):
            return "Expression contains unsupported characters."
        value = eval(expression)
        return str(value)
    except Exception as e:
        return f"Invalid expression: {e}"

# Manual test
calculator_tool("999 * 38")
```

```python
# COMMAND ----------
# STEP 7 – Optional TOOL: SQL over Lakehouse (requires Spark)

def sql_tool(query: str) -> str:
    """
    Execute a SQL query using Spark and return a small preview as JSON string.
    """
    try:
        df = spark.sql(query)
        pdf = df.limit(10).toPandas()
        return pdf.to_json(orient="records")
    except Exception as e:
        return f"SQL error: {e}"

# Example (will only work if the table exists in your workspace):
# sql_tool("SELECT COUNT(*) AS cnt FROM training.silver.orders_clean")
```

```python
# COMMAND ----------
# STEP 8 – Define TOOL Schemas for Function Calling

# Tools in OpenAI / Databricks Foundation Models use the "type": "function" schema.
# The model will decide when and how to call these tools.

tools = [
    {
        "type": "function",
        "function": {
            "name": "rag_search",
            "description": "Retrieve knowledge using vector search over the internal training notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language question to search in the training notes.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a simple arithmetic expression like '999 * 38'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Math expression to evaluate.",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "sql_query",
            "description": "Run a SQL query on the Databricks Lakehouse (Spark SQL). Returns up to 10 rows as JSON.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Valid SQL query to run with spark.sql.",
                    }
                },
                "required": ["query"],
            },
        },
    },
]

# Map tool names to Python callables
def rag_search(query: str) -> str:
    """Wrapper for rag_tool that returns JSON string."""
    return json.dumps(rag_tool(query), indent=2)

def calculator(expression: str) -> str:
    return calculator_tool(expression)

def sql_query(query: str) -> str:
    return sql_tool(query)

tool_functions = {
    "rag_search": rag_search,
    "calculator": calculator,
    "sql_query": sql_query,
}
```

```python
# COMMAND ----------
# STEP 9 – Build the Agent (Planner + Tool Execution Loop)

def agent(user_query: str, debug: bool = False) -> str:
    """
    Compound AI Agent:
    - Sends the user query + tool schema to the LLM
    - Lets the LLM decide whether to call tools
    - Executes tools, returns results to LLM
    - Returns final grounded answer to the caller
    """

    # System prompt: explain tools & behavior
    system_prompt = """
    You are a helpful enterprise assistant.
    You have access to these tools:
    - rag_search(query): use this to retrieve accurate information from training notes about Databricks, Delta Lake, MLflow, Unity Catalog, and DLT.
    - calculator(expression): use this for arithmetic.
    - sql_query(query): use this to run SQL on the Lakehouse when the user explicitly asks to run SQL.
    
    Decide which tool(s) to use, call them using function calling, and then synthesize a clear final answer.
    Always ground explanations in the retrieved context when you use rag_search.
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
    ]

    # --------- First LLM call: decide whether to call tools ---------
    response = client.chat.completions.create(
        model=FOUNDATION_MODEL_NAME,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        temperature=0.1,
    )

    ai_msg = response.choices[0].message

    if debug:
        print("=== First LLM Response ===")
        print(ai_msg)

    # If the model didn't request any tool calls, just return its answer
    if not ai_msg.tool_calls:
        return ai_msg.content

    # --------- Execute all requested tools ---------
    messages.append(ai_msg)  # include the tool_call message in the conversation

    for tool_call in ai_msg.tool_calls:
        function_name = tool_call.function.name
        function_args = tool_call.function.arguments

        if debug:
            print(f"\nTool requested: {function_name}")
            print("Raw args:", function_args)

        tool_fn = tool_functions.get(function_name)
        if tool_fn is None:
            tool_output = f"Unknown tool: {function_name}"
        else:
            try:
                parsed_args = json.loads(function_args) if function_args else {}
            except json.JSONDecodeError:
                parsed_args = {}
            tool_output = tool_fn(**parsed_args)

        if debug:
            print("Tool output:", tool_output)

        # Add tool result to messages
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_output,
            }
        )

    # --------- Second LLM call: use tool results to answer ---------
    final_response = client.chat.completions.create(
        model=FOUNDATION_MODEL_NAME,
        messages=messages,
        temperature=0.1,
    )

    final_msg = final_response.choices[0].message
    return final_msg.content
```

```python
# COMMAND ----------
# STEP 10 – Test 1: RAG Tool through the Agent

response = agent("What is Delta Lake and why is it useful in Databricks?")
print(response)
```

```python
# COMMAND ----------
# STEP 11 – Test 2: Calculator Tool through the Agent

response = agent("What is 999 * 38?")
print(response)
```

```python
# COMMAND ----------
# STEP 12 – Test 3: Multi-step Reasoning (RAG + Calculator)

response = agent(
    "Using the training notes, explain what MLflow is, and then compute 36 * 14."
)
print(response)
```

```python
# COMMAND ----------
# STEP 13 – Test 4: Explicit SQL Tool (Optional)

# This will only work if the table exists in your workspace.
# Replace table name with something real in your environment.

response = agent(
    "Run SQL: SELECT 1 AS sample_value"
)
print(response)
```

```python
# COMMAND ----------
# STEP 14 – Test 5: "Plan your approach" (Agent-style reasoning)

response = agent("Plan your approach step by step, then answer: What is Unity Catalog?")
print(response)
```

---





 -->



-----------


<!-- 
#  **LAB 6 — RAG with Tools + Agents (Compound AI)**

### *(Agents + RAG + Tools + Reasoning Chains)*

### **Learning Objectives**

By the end of this lab, learners will:

✔ Understand what an *Agent* is
✔ Build a **Tool-enabled RAG Agent**
✔ Use **Function Calling / Tool Calling**
✔ Implement a **planning + retrieval + reasoning** loop
✔ Use RAG as a “Retriever Tool” inside the Agent
✔ Integrate external tools (calculator, search, SQL, etc.)

---

#  **STEP 1 — What Is an Agent? (Explain to Students)**


An **Agent** is an AI system that can:

1. **Plan** → Decide what tools to use
2. **Act** → Call tools (retrieval, search, SQL, calculator, etc.)
3. **Reason** → Interpret tool results
4. **Respond** → Give final answer

This is the foundation of modern **Compound AI Systems** (OpenAI, Databricks, Anthropic).

RAG becomes **one tool** inside the agent — the *retriever tool*.

---


#  **STEP 2 — Build RAG as a Tool (Retriever Tool)**


You already built:

* chunks
* embeddings
* vector index

Now convert the RAG retriever into an **agent tool**.

```python
def rag_tool(query):
    # embed question
    q_emb = model.encode(query)

    # similarity search
    sims = np.dot(vectors, q_emb)
    top_idx = sims.argsort()[-3:][::-1]

    context = "\n".join(chunks[i] for i in top_idx)

    return {
        "context": context,
        "top_chunks": [chunks[i] for i in top_idx]
    }
```

---



#  **STEP 3 — Add Another Tool (Calculator Example)**


Agents become MORE powerful with multiple tools.

```python
def calculator_tool(expression):
    try:
        return str(eval(expression))
    except:
        return "Invalid expression"
```

---


#  **STEP 4 — Define Agent Tools for LLM (Tool Schema)**


LLMs need structured metadata to know how to call tools.

```python
tools = [
    {
        "name": "rag_search",
        "description": "Retrieve knowledge using vector search",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "calculator",
        "description": "Perform calculation",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string"}
            },
            "required": ["expression"]
        }
    }
]
```

---


#  **STEP 5 — Build the AGENT (Planner + Tool Execution)**


This example uses DBRX or any LLM with function calling.

```python
from databricks import llm

def agent(query):

    # step 1 → ask LLM what to do
    response = llm.chat(
        messages = [
            {"role": "user", "content": query}
        ],
        tools = tools
    )

    # step 2 → If LLM wants to call a tool
    if "tool_calls" in response:
        tool_call = response["tool_calls"][0]
        tool_name = tool_call["name"]
        args = tool_call["args"]

        # execute tool
        if tool_name == "rag_search":
            result = rag_tool(args["query"])
        elif tool_name == "calculator":
            result = calculator_tool(args["expression"])
        else:
            result = "Unknown tool"

        # step 3 → send tool result back to LLM
        response2 = llm.chat(
            messages=[
                {"role": "user", "content": query},
                {"role": "tool", "tool_name": tool_name, "content": str(result)}
            ]
        )
        return response2["message"]

    # normal case (no tool needed)
    return response["message"]
```

---


#  **STEP 6 — Test Your Compound AI Agent**


### Test RAG tool through the agent:

```python
agent("What is Delta Lake?")
```

Expected:

```
Delta Lake ensures ACID transactions...
```

---

### Test Calculator tool through the agent:

```python
agent("What is 999 * 38?")
```

Expected:

```
999 * 38 = 37962
```

---

### Test multi-step reasoning:

```python
agent("Using the training notes, explain MLflow and compute 36*14.")
```

Expected behavior:

* Agent retrieves MLflow description using RAG tool
* Agent uses calculator tool for math
* Agent writes combined explanation

---


#  **STEP 7 — Build Chain-of-Thought Reasoning (Hidden)**

Databricks DBRX doesn't reveal chain-of-thought but supports planning implicitly.

To force chain-style behavior:

```python
agent("Plan your approach step by step, then answer: What is Delta Lake?")
```

LLM should:

1. Decide to call `rag_search`
2. Retrieve context
3. Produce final grounded answer

---

#  **STEP 8 — Add External Tool (Optional: SQL Query Tool)**


This demonstrates how to integrate enterprise data tools.

```python
def sql_tool(query):
    df = spark.sql(query)
    return df.toPandas().to_dict()
```

Add to tools:

```python
tools.append({
    "name": "sql_query",
    "description": "Run SQL queries on Lakehouse",
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"]
    }
})
```

Now your agent can answer:

```python
agent("Run SQL: SELECT COUNT(*) FROM training.silver.orders_clean")
```

---

 -->
