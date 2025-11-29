
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


