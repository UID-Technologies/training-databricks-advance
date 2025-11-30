#  LAB 9 — Build a Multi-Agent Knowledge Assistant

##  Goal

Build a **chat-style Knowledge Assistant** that:

* Uses **RAG** over your documents
* Uses **multiple tools/agents** (RAG, SQL, Calculator, FAQ, Summary)
* Maintains **conversation history**
* Uses a **Planner Agent** to decide which tools to call
* Produces friendly, grounded answers like a real enterprise assistant

You can implement this **inside Databricks** (notebook-based chat loop) or **wired to your FastAPI RAG API** from Lab 8.

---

##  Architecture Overview

Your Multi-Agent Knowledge Assistant will look like this:

```text
User Question
      ↓
Conversation Memory + History
      ↓
Planner Agent (LLM)
      ↓
One or More Tools:
   - RAG Tool (vector search)
   - FAQ Tool (simple lookup)
   - SQL Tool (Lakehouse data)
   - Calculator Tool
   - Summarizer Tool
      ↓
Tool Outputs
      ↓
Response Agent / Supervisor
      ↓
Final Friendly Answer
```

---

##  Prerequisites

From previous labs, you should already have:

* **Chunks + embeddings** from PDFs / text (Lab 2–3)
* **FAISS or NumPy-based vector search** (Lab 3)
* **RAG function** (Lab 4)
* **MLflow embedder (optional)** (Lab 4–5)
* **Databricks LLM access or external LLM (OpenAI/DBRX)**
* (Optional) **RAG FastAPI API** (Lab 8)

We’ll now wrap all that into an **interactive assistant**.

---

#  STEP 1 — Define Knowledge Sources

You’ll combine **multiple knowledge types**:

1. **RAG Knowledge**: your prepared chunks + embeddings
2. **FAQ Knowledge**: simple in-memory FAQ dictionary
3. **SQL Knowledge**: metrics or tables in Lakehouse
4. **Conversation History**: past chat messages

### 1.1 – Setup FAQ Data

```python
faq_knowledge = {
    "what is delta lake": "Delta Lake is a storage layer that brings ACID transactions to big data workloads.",
    "what is unity catalog": "Unity Catalog is Databricks' unified governance solution for data and AI assets.",
    "what is mlflow": "MLflow is an open-source platform for managing the ML lifecycle: tracking, models, and deployment."
}
```

---

#  STEP 2 — Implement Core Tools (Worker Agents)

We’ll reuse and slightly extend what you had in Labs 6–7.

### 2.1 – RAG Tool (Vector Search + Context)

Assuming you already have `vectors`, `chunks`, and `model`:

```python
import numpy as np

def rag_tool(query: str, top_k: int = 3):
    q_emb = model.encode(query)
    sims = np.dot(vectors, q_emb)
    top_idx = sims.argsort()[-top_k:][::-1]
    
    retrieved_chunks = [chunks[i] for i in top_idx]
    context = "\n".join(retrieved_chunks)
    
    return {
        "type": "rag_result",
        "query": query,
        "context": context,
        "chunks": retrieved_chunks
    }
```

---

### 2.2 – FAQ Tool

```python
def faq_tool(query: str):
    key = query.lower().strip()
    for faq_q, answer in faq_knowledge.items():
        if faq_q in key:
            return {
                "type": "faq_result",
                "question": faq_q,
                "answer": answer
            }
    return {
        "type": "faq_result",
        "answer": None
    }
```

---

### 2.3 – SQL Tool (Optional, if you have tables)

```python
def sql_tool(sql_query: str):
    try:
        df = spark.sql(sql_query)
        return {
            "type": "sql_result",
            "query": sql_query,
            "rows": df.limit(20).toPandas().to_dict(orient="records")
        }
    except Exception as e:
        return {"type": "sql_result", "error": str(e)}
```

---

### 2.4 – Calculator Tool

```python
def calculator_tool(expression: str):
    try:
        result = eval(expression)
        return {
            "type": "calc_result",
            "expression": expression,
            "result": result
        }
    except Exception as e:
        return {
            "type": "calc_result",
            "error": str(e)
        }
```

---

### 2.5 – Summarizer Tool (using LLM)

```python
from databricks import llm

def summarizer_tool(text: str):
    prompt = f"Summarize the following text in 3-5 bullet points:\n\n{text}"
    summary = llm.chat(prompt)
    return {
        "type": "summary_result",
        "summary": summary
    }
```

---

#  STEP 3 — Define Tools Schema (for Planner LLM)

We’ll give the Planner Agent a view of available tools.

```python
tools = [
    {
        "name": "rag_tool",
        "description": "Use this to answer questions about technical training, Databricks, Delta Lake, MLflow, etc., using RAG.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    },
    {
        "name": "faq_tool",
        "description": "Use this for very common FAQ-style questions (what is Delta Lake, what is MLflow, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"]
        }
    },
    {
        "name": "sql_tool",
        "description": "Use this to run SQL on the Lakehouse when user asks for metrics, counts, or analytics.",
        "input_schema": {
            "type": "object",
            "properties": {"sql_query": {"type": "string"}},
            "required": ["sql_query"]
        }
    },
    {
        "name": "calculator_tool",
        "description": "Use this to do math or numeric calculations.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"]
        }
    },
    {
        "name": "summarizer_tool",
        "description": "Use this to summarize long text for the user.",
        "input_schema": {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"]
        }
    }
]
```

---

#  STEP 4 — Add Conversation History (Memory)

Simple in-notebook memory:

```python
conversation_history = []

def add_message(role, content):
    conversation_history.append({"role": role, "content": content})

def get_recent_history(n=6):
    return conversation_history[-n:]
```

Every time user sends a query, you’ll append:

```python
add_message("user", user_query)
```

And when assistant responds:

```python
add_message("assistant", answer)
```

---

#  STEP 5 — Planner Agent

The Planner decides **which tools to use** based on:

* User query
* Recent conversation history

> Note: Exact function-calling syntax may differ based on DBRX / API. We’ll keep it conceptual and simple.

```python
from databricks import llm

def planner_agent(user_query: str):
    history = get_recent_history()
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history])

    planner_prompt = f"""
You are a planner agent for a knowledge assistant.

You have these tools:
- rag_tool: for RAG-based enterprise/document questions
- faq_tool: for simple FAQs
- sql_tool: for Lakehouse data questions (SQL)
- calculator_tool: for math
- summarizer_tool: for summarizing text

User query:
{user_query}

Recent conversation:
{history_text}

Decide:
1) Which single tool is best to call first.
2) Provide the JSON payload for that tool.

Respond ONLY as JSON of the form:
{{"tool_name": "...", "args": {{...}}}}
    """

    plan_text = llm.chat(planner_prompt)
    return plan_text
```

You may need to:

```python
import json
plan = json.loads(plan_text)
```

---

# 🛠 STEP 6 — Tool Executor + Supervisor

### 6.1 – Tool Executor

```python
import json

def execute_tool(plan_json: str):
    plan = json.loads(plan_json)
    tool_name = plan["tool_name"]
    args = plan["args"]

    if tool_name == "rag_tool":
        return rag_tool(**args)
    if tool_name == "faq_tool":
        return faq_tool(**args)
    if tool_name == "sql_tool":
        return sql_tool(**args)
    if tool_name == "calculator_tool":
        return calculator_tool(**args)
    if tool_name == "summarizer_tool":
        return summarizer_tool(**args)

    return {"error": f"Unknown tool: {tool_name}"}
```

---

### 6.2 – Supervisor / Response Agent

This agent combines:

* User question
* Tool output
* Conversation history

To produce a **final, natural answer**.

```python
def response_agent(user_query: str, tool_result: dict):
    history = get_recent_history()
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history])

    prompt = f"""
You are a helpful Knowledge Assistant for Databricks and RAG topics.

User question:
{user_query}

Conversation so far:
{history_text}

Tool result (JSON):
{tool_result}

Using ONLY the information from the tool result and conversation history, answer the user in a friendly way.

If tool_result contains 'context' or 'chunks', use them as the source of truth.
If the information is not present, say: "I don't know based on the available data."
    """

    answer = llm.chat(prompt)
    return answer
```

---

#  STEP 7 — Interactive Chat Loop

Now create a simple chat loop in the notebook.

```python
def knowledge_assistant_chat(user_query: str):
    # 1. Store user message
    add_message("user", user_query)

    # 2. Ask planner which tool to use
    plan_text = planner_agent(user_query)
    print("PLANNER DECISION:", plan_text)

    # 3. Execute tool
    tool_result = execute_tool(plan_text)
    print("TOOL RESULT:", tool_result)

    # 4. Get final answer from response agent
    answer = response_agent(user_query, tool_result)
    print("ASSISTANT:", answer)

    # 5. Store assistant message
    add_message("assistant", answer)

    return answer
```

---

#  STEP 8 — Test the Multi-Agent Knowledge Assistant

### 8.1 – RAG Question

```python
knowledge_assistant_chat("What is Delta Lake and why is it important?")
```

Expected behavior:

* Planner chooses `rag_tool` or `faq_tool`
* RAG retrieves relevant chunks
* Response agent synthesizes a friendly answer

---

### 8.2 – SQL Question

```python
knowledge_assistant_chat("How many orders are there in training.silver.orders_clean?")
```

Expected:

* Planner chooses `sql_tool`
* SQL runs
* Response agent summarizes row count in words

---

### 8.3 – Math + Description

```python
knowledge_assistant_chat("Explain what MLflow is and also calculate 256 * 78.")
```

You might see:

* First tool: `rag_tool` or `faq_tool`
* Second invocation (you can extend Planner) → `calculator_tool`
* Response agent merges results.

(For now, Lab can stick to single-tool per query. As an extension, you can evolve it to multi-step planning.)

---

# 🎓 What Learners Achieve in LAB 9

By now, they have:

- A multi-agent **Knowledge Assistant**
- Tools for RAG, FAQ, SQL, Calculator, Summary
- A Planner Agent that routes queries
- A Response Agent that generates final answers
- Conversation history acting as simple memory
- Understanding of Compound AI / Agentic Architectures

This is a **full end-to-end, realistic AI Assistant** pattern usable in enterprise.

---
