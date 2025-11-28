
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

---
