
#  **LAB 7 — Multi-Agent Reasoning Chains (Planner + Worker Agents)**

### **Goal**

Learners build a **multi-agent system** where:

* One **Planner Agent** decides the steps
* Multiple **Worker Agents** execute the steps
* A final **Supervisor Agent** assembles the final answer

This is the backbone of **Compound AI Systems**.

---

#  **Architecture of Multi-Agent System**

```
                   ┌─────────────────┐
                   │  User Question  │
                   └────────┬────────┘
                            │
                    (1) Planner Agent
                            │
     ┌──────────────┬─────────────┬──────────────┐
     │              │             │              │
 Retriever Agent   SQL Agent   Calculator     Summarizer
     │              │             │              │
      └────────────┴─────────────┴─────────────┘
                    │
            (3) Supervisor Agent
                    │
                    ▼
             Final Answer (LLM)
```

---


 **single, self-contained Databricks notebook** that:

* Reuses your **served embedding model** (`test-endpoint` from Lab 5)
* Reuses your **chat LLM endpoint** (`databricks-meta-llama-3-1-405b-instruct`)
* Implements **Planner → Worker Agents → Supervisor**
* Uses **proper Databricks function calling** (with `tool_call_id`, `function.name`, `function.arguments`)

You can paste this **as-is** into a new notebook.


---

##  STEP 0 — Imports & Shared Setup

```python
# COMMAND ----------
import json
import numpy as np
import pandas as pd
import requests
```

---

##  STEP 1 — Tokens, Workspace, Endpoints

* **Embedding endpoint**: your MLflow model from Lab 5 → `test-endpoint`
* **LLM endpoint**: foundation model → `databricks-meta-llama-3-1-405b-instruct`

```python
# COMMAND ----------
# Get workspace + token
workspace = spark.conf.get("spark.databricks.workspaceUrl")
token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

# Embedding endpoint (from Lab 5)
EMBED_ENDPOINT_NAME = "test-endpoint"   # UC MLflow model serving endpoint
EMBED_URL = f"https://{workspace}/serving-endpoints/{EMBED_ENDPOINT_NAME}/invocations"

# LLM endpoint (with function calling)
LLM_ENDPOINT_NAME = "databricks-meta-llama-3-1-405b-instruct"
LLM_URL = f"https://{workspace}/serving-endpoints/{LLM_ENDPOINT_NAME}/invocations"

HEADERS = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
```

---

##  STEP 2 — Helper: Embedding via Served Model

```python
# COMMAND ----------
def embed(texts):
    """
    Call the served embedding model (MLflow endpoint) to get embeddings.
    texts: list[str]
    returns: list[list[float]]
    """
    payload = {"inputs": texts}
    resp = requests.post(EMBED_URL, headers=HEADERS, data=json.dumps(payload))
    resp.raise_for_status()
    data = resp.json()
    return data["predictions"]
```

---

##  STEP 3 — Load Chunks & Embeddings (from Lab 4/5)

```python
# COMMAND ----------
df_chunks = spark.read.format("delta").load("/Volumes/workspace/lab/myvolume/prepared_chunks")
pdf_chunks = df_chunks.toPandas()

chunks = pdf_chunks["chunk"].tolist()
vectors = np.stack(pdf_chunks["embedding"].apply(lambda x: np.array(x, dtype="float32")).values)

print("Loaded chunks:", len(chunks))
print("Embedding matrix shape:", vectors.shape)
```

---

##  STEP 4 — LLM Client + Response Normalizer

```python
# COMMAND ----------
class DatabricksLLM:
    def __init__(self, url: str):
        self.url = url
        self.token = token

    def chat(self, messages, tools=None):
        payload = {"messages": messages}
        if tools:
            payload["tools"] = tools

        resp = requests.post(
            self.url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            },
            data=json.dumps(payload)
        )
        resp.raise_for_status()
        return resp.json()


def extract_message(response: dict) -> dict:
    """
    Normalize Databricks FM chat completion response into:
    {
      "content": str | None,
      "tool_calls": list | None
    }
    """
    # We know the structure from previous debug:
    # { "choices": [ { "message": { "content": ..., "tool_calls": [...] } } ] }
    if "choices" in response and response["choices"]:
        msg = response["choices"][0]["message"]
        return {
            "content": msg.get("content"),
            "tool_calls": msg.get("tool_calls")
        }

    # Fallbacks
    if "message" in response:
        msg = response["message"]
        if isinstance(msg, str):
            return {"content": msg, "tool_calls": None}
        return {
            "content": msg.get("content"),
            "tool_calls": msg.get("tool_calls")
        }

    if "output_text" in response:
        return {"content": response["output_text"], "tool_calls": None}

    return {"content": str(response), "tool_calls": None}


llm = DatabricksLLM(LLM_URL)
```

---

##  STEP 5 — Worker Agents (Tools)

### 5.1 RAG Worker (uses served embeddings + chunks)

```python
# COMMAND ----------
def rag_worker(query: str) -> dict:
    """
    RAG worker:
    - Embed query via served model
    - Similarity search on stored chunk embeddings
    - Return top-3 context
    """
    q_emb = np.array(embed([query])[0], dtype="float32")
    sims = np.dot(vectors, q_emb)
    top_idx = sims.argsort()[-3:][::-1]

    top_chunks = [chunks[i] for i in top_idx]
    context = "\n\n".join(top_chunks)

    return {"context": context, "top_chunks": top_chunks}
```

### 5.2 SQL Worker

```python
# COMMAND ----------
def sql_worker(query: str) -> dict:
    """
    SQL worker:
    - Execute Spark SQL
    - Return up to 10 rows as JSON
    """
    try:
        df = spark.sql(query)
        pdf = df.limit(10).toPandas()
        return {"rows": json.loads(pdf.to_json(orient="records"))}
    except Exception as e:
        return {"error": f"SQL error: {e}"}
```

### 5.3 Calculator Worker

```python
# COMMAND ----------
def calc_worker(expression: str) -> dict:
    """
    Calculator worker.
    Very simple, demo only. Eval restricted to basic chars.
    """
    allowed = "0123456789+-*/(). "
    if not all(c in allowed for c in expression):
        return {"result": "Invalid characters in expression"}

    try:
        value = eval(expression)
        return {"result": value}
    except Exception as e:
        return {"result": f"Error: {e}"}
```

### 5.4 Summarizer Worker (calls LLM directly)

```python
# COMMAND ----------
def summary_worker(text: str) -> dict:
    """
    Summarizer worker:
    - Calls same LLM endpoint to summarize text.
    """
    messages = [
        {"role": "system", "content": "You are a concise summarizer."},
        {"role": "user", "content": f"Summarize the following text:\n\n{text}"}
    ]
    raw = llm.chat(messages)
    msg = extract_message(raw)
    return {"summary": msg["content"]}
```

---

##  STEP 6 — Tool Schemas (for Planner Agent)

```python
# COMMAND ----------
tools = [
    {
        "type": "function",
        "function": {
            "name": "rag_worker",
            "description": "Retrieve Databricks training context using RAG.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Natural language question for RAG."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "sql_worker",
            "description": "Run a SQL query on the Lakehouse using Spark SQL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query to execute."}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calc_worker",
            "description": "Perform arithmetic calculations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression, e.g., '89 * 42'."}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summary_worker",
            "description": "Summarize a longer piece of text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to summarize."}
                },
                "required": ["text"]
            }
        }
    }
]

tool_functions = {
    "rag_worker": rag_worker,
    "sql_worker": sql_worker,
    "calc_worker": calc_worker,
    "summary_worker": summary_worker,
}
```

---

##  STEP 7 — Planner Agent

Planner decides **which worker** to call for a given query.

```python
# COMMAND ----------
def planner_agent(user_query: str) -> dict:
    """
    Planner Agent:
    - Receives user_query
    - Decides which tool (worker) to use and with what arguments
    """
    system_prompt = """
    You are a Planner Agent in a multi-agent system.

    Available tools:
    - rag_worker(query): for knowledge / documentation questions
    - sql_worker(query): when the user explicitly asks to RUN SQL
    - calc_worker(expression): for arithmetic
    - summary_worker(text): when asked to summarize something

    Decide which single tool is most appropriate for the user query.
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query}
    ]

    raw = llm.chat(messages, tools=tools)
    msg = extract_message(raw)
    return msg  # contains content=None and tool_calls if any
```

---

##  STEP 8 — Tool Executor

```python
# COMMAND ----------
def execute_tool_call(tool_call: dict) -> dict:
    """
    Executes a single tool_call from the LLM.
    Expects Databricks/OpenAI style:
    {
      "id": "...",
      "type": "function",
      "function": {
        "name": "...",
        "arguments": "{...json...}"
      }
    }
    """
    fn = tool_call["function"]
    tool_name = fn["name"]
    args_json = fn["arguments"]
    args = json.loads(args_json) if args_json else {}

    worker = tool_functions.get(tool_name)
    if worker is None:
        return {"error": f"Unknown tool: {tool_name}"}

    return {
        "tool_name": tool_name,
        "tool_call_id": tool_call["id"],
        "result": worker(**args)
    }
```

---

##  STEP 9 — Supervisor Agent

Takes original query + worker result and produces final answer.

```python
# COMMAND ----------
def supervisor_agent(user_query: str, tool_result_bundle: dict) -> str:
    """
    Supervisor Agent:
    - Gets original user_query
    - Gets structured tool result
    - Produces final answer for the user
    """
    system_prompt = """
    You are a Supervisor Agent.

    You receive:
    - The original user query
    - The result from one worker tool

    Your job:
    - Explain briefly what was done
    - Use the worker result to answer the query
    - Be clear and concise
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_query},
        {
            "role": "tool",
            "content": json.dumps(tool_result_bundle, indent=2)
        }
    ]

    raw = llm.chat(messages)
    msg = extract_message(raw)
    return msg["content"]
```

---

##  STEP 10 — Multi-Agent Orchestrator

```python
# COMMAND ----------
def multi_agent(query: str, debug: bool = False) -> str:
    """
    Orchestrates:
    - Planner Agent
    - Worker Agent
    - Supervisor Agent
    """
    # 1. Planner decides workflow
    if debug:
        print("=== Planner Phase ===")

    planner_msg = planner_agent(query)
    if debug:
        print("Planner response:", planner_msg)

    tool_calls = planner_msg.get("tool_calls")
    if not tool_calls:
        # Planner chose to answer directly
        return planner_msg["content"]

    # For simplicity: handle only the first tool_call
    tool_call = tool_calls[0]

    # 2. Execute worker
    if debug:
        print("\n=== Worker Phase ===")
        print("Tool call:", tool_call)

    worker_bundle = execute_tool_call(tool_call)

    if debug:
        print("Worker result:", worker_bundle)

    # 3. Supervisor composes final answer
    if debug:
        print("\n=== Supervisor Phase ===")

    final_answer = supervisor_agent(query, worker_bundle)
    return final_answer
```

---

##  STEP 11 — Test the Multi-Agent System

### 11.1 Pure RAG Query

```python
# COMMAND ----------
print(multi_agent("What is Delta Lake? Explain briefly.", debug=True))
```

---

### 11.2 SQL Query

```python
# COMMAND ----------
print(multi_agent("Run SQL: SELECT COUNT(*) FROM training.silver.orders_clean", debug=True))
```

(Adjust the table name to one that exists in your workspace.)

---

### 11.3 Multi-Step MLflow + Math

```python
# COMMAND ----------
print(multi_agent("Using the training notes, explain MLflow and then compute 89 * 42.", debug=True))
```

---


<!-- 
#  **STEP 1 — Define Worker Tools (Agents)**


## 1 RAG Agent Tool

```python
def rag_worker(query):
    q_emb = model.encode(query)
    sims = np.dot(vectors, q_emb)
    top = sims.argsort()[-3:][::-1]
    context = "\n".join(chunks[i] for i in top)
    return {"context": context}
```

## 2 SQL Agent Tool

```python
def sql_worker(query):
    df = spark.sql(query)
    return df.toPandas().to_dict()
```

## 3 Calculator Agent Tool

```python
def calc_worker(expression):
    try:
        return {"result": eval(expression)}
    except:
        return {"result": "Error"}
```

## 4 Summarizer Tool

```python
def summary_worker(text):
    from databricks import llm
    return {"summary": llm.chat(f"Summarize:\n{text}")}
```

---


#  **STEP 2 — Define Tool Schemas**

LLM needs a JSON schema for each tool.

```python
tools = [
    {
        "name": "rag_worker",
        "description": "Retrieve context using RAG",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    },
    {
        "name": "sql_worker",
        "description": "Run SQL queries on Lakehouse",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    },
    {
        "name": "calc_worker",
        "description": "Calculator for arithmetic",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"]
        }
    },
    {
        "name": "summary_worker",
        "description": "Summarize any text",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"]
        }
    }
]
```

---


#  **STEP 3 — The Planner Agent (Decides the Workflow)**


The planner chooses **which Worker Agent(s)** to call and in what order.

```python
from databricks import llm

def planner_agent(user_query):
    return llm.chat(
        messages=[{"role": "user", "content": f"PLAN: {user_query}"}],
        tools=tools
    )
```

Example Planner Output:

```
I will retrieve context using RAG.
Tool call: rag_worker(query="What is Delta Lake?")
```

---


#  **STEP 4 — Tool Executor (Executes Worker Agents)**


Planner decides → Executor runs it.

```python
def execute_tool(tool_call):
    name = tool_call["name"]
    args = tool_call["args"]

    if name == "rag_worker":
        return rag_worker(**args)
    if name == "sql_worker":
        return sql_worker(**args)
    if name == "calc_worker":
        return calc_worker(**args)
    if name == "summary_worker":
        return summary_worker(**args)

    return {"error": "Unknown tool"}
```

---

#  **STEP 5 — The Supervisor Agent (Final Answer)**


Combines tool outputs → Creates final answer.

```python
def supervisor_agent(user_query, tool_result):
    return llm.chat(
        messages=[
            {"role": "user", "content": user_query},
            {"role": "tool", "tool_name": "worker", "content": str(tool_result)}
        ]
    )["message"]
```

---


#  **STEP 6 — Multi-Agent Orchestrator (Main Function)**

```python
def multi_agent(query):

    # 1. Planner decides what to do
    plan = planner_agent(query)

    if "tool_calls" not in plan:
        return plan["message"]

    # 2. Execute the tool
    tool_call = plan["tool_calls"][0]
    result = execute_tool(tool_call)

    # 3. Supervisor builds final answer
    final = supervisor_agent(query, result)

    return final
```

---


#  **STEP 7 — Test Multi-Agent Reasoning**


###  Test a pure RAG query

```python
multi_agent("What is Delta Lake?")
```

###  Test SQL

```python
multi_agent("Run SQL: SELECT COUNT(*) FROM training.silver.orders_clean")
```

###  Test multi-step reasoning

```python
multi_agent("Using the training notes, explain MLflow and compute 89 * 42")
```

### Expected Output

* Planner decides the workflow
* RAG Agent retrieves context
* Calculator computes
* Supervisor merges results

--- -->
