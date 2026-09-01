# Project 02: Agentic Job Search Assistant — Technical Roadmap

## 1. What We're Building

A conversational AI agent that receives natural language requests, **reasons** about what to do, **calls tools** (P1's capabilities), **observes** results, and **decides** what to do next — in a loop — until it can answer the user.

This is not a chatbot with hardcoded commands. The LLM itself decides which tools to call, in what order, with what arguments, based on the conversation.

---

## 2. P1 Capabilities → Agent Tools

P1 has 5 distinct capabilities that become tools the agent can invoke. Each tool needs: a name, a natural language description (so the LLM understands when to use it), a parameter schema (so the LLM generates valid arguments), and a function that executes the action.

### Tool Inventory

| Tool Name | What It Wraps in P1 | Input | Output | When the Agent Should Use It |
|---|---|---|---|---|
| `scrape_jobs` | `helper.run_pipeline()` → `fetch_LinkedIn_jobs.main()` + `ingest_jobs()` | (none, or optional: keywords, location to customize search URL) | `{ status, jobs_count }` | User wants fresh data, or data is stale |
| `search_jobs` | `embed_jobs.Search()` | `query: str, limit: int` | List of jobs with similarity scores | User asks a question like "find me X jobs" |
| `match_all_jobs` | Matching engine: `match_job()` over all Qdrant records | `limit: int` | Ranked list with multi-factor score breakdowns (skills, responsibilities, experience, seniority) | User wants to see best matches against their CV |
| `tailor_cv` | `groq_client.generate_tailored_recommendation()` | `top_n: int` (uses last match results from shared state) | LLM-generated match reasons + tailored CV bullets | User wants CV tailored for specific jobs |
| `get_job_stats` | `QdrantClient.get_collection()` | (none) | `{ total_jobs, collection_name }` | Agent needs to check if data exists before searching |

### Tool Dependencies & Shared State

Some tools depend on others' results:

```
scrape_jobs → populates Qdrant → enables search_jobs & match_all_jobs
match_all_jobs → stores results in shared state → enables tailor_cv
```

The agent needs a **shared state dict** that tools can read/write:

```
state = {
    "last_matches": [...],      # set by match_all_jobs, read by tailor_cv
    "last_search_results": [...] # set by search_jobs (optional, for future use)
}
```

> **IMPORTANT:** `tailor_cv` depends on `match_all_jobs` having run first. If the agent calls `tailor_cv` without prior matches, the tool returns an error, and the agent should reason: "I need to run match_all_jobs first."

### Tool Schema Format (Groq / OpenAI Function Calling)

Each tool is described to Groq in this JSON format:

```json
{
  "type": "function",
  "function": {
    "name": "search_jobs",
    "description": "Search the vector database for jobs matching a query using semantic similarity. Returns jobs ranked by relevance. Use this when the user wants to explore what jobs are available.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "Natural language query describing the type of job to search for"
        },
        "limit": {
          "type": "integer",
          "description": "Maximum number of results (default 5)"
        }
      },
      "required": ["query"]
    }
  }
}
```

The LLM reads these schemas and decides:
1. **Whether** to call a tool (or just respond with text)
2. **Which** tool to call
3. **What arguments** to pass

The LLM generates tool calls as structured JSON — not free-form text. This is why function calling is the foundation of tool use.

---

## 3. The ReAct Loop — How the Agent Thinks

ReAct = **Re**ason + **Act**. The agent alternates between reasoning (thinking about what to do) and acting (calling tools), observing results after each action.

### Execution Flow

```
┌─────────────────────────────────────────────────────┐
│                    USER MESSAGE                      │
│           "Find me Python backend jobs"              │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│              AGENT REASONING (LLM call)              │
│                                                      │
│  Input: system prompt + conversation history + tools │
│  Output: either TOOL CALL or TEXT RESPONSE           │
│                                                      │
│  LLM thinks: "User wants Python jobs. I should       │
│  first check if there's data, then search."          │
│  → Decides: call get_job_stats()                     │
└──────────────────────┬──────────────────────────────┘
                       │ tool_call
                       ▼
┌─────────────────────────────────────────────────────┐
│              TOOL EXECUTION                          │
│                                                      │
│  Execute: get_job_stats()                            │
│  Result: { "total_jobs": 45, "collection": "jobs" }  │
│                                                      │
│  → Result added to conversation as "tool" message    │
└──────────────────────┬──────────────────────────────┘
                       │ loop back
                       ▼
┌─────────────────────────────────────────────────────┐
│              AGENT REASONING (LLM call #2)           │
│                                                      │
│  LLM sees: 45 jobs available.                        │
│  LLM thinks: "Good, there's data. Now search for     │
│  Python backend jobs."                               │
│  → Decides: call search_jobs("python backend", 5)    │
└──────────────────────┬──────────────────────────────┘
                       │ tool_call
                       ▼
┌─────────────────────────────────────────────────────┐
│              TOOL EXECUTION                          │
│                                                      │
│  Execute: search_jobs("python backend", 5)           │
│  Result: [ { title, company, score, ... }, ... ]     │
└──────────────────────┬──────────────────────────────┘
                       │ loop back
                       ▼
┌─────────────────────────────────────────────────────┐
│              AGENT REASONING (LLM call #3)           │
│                                                      │
│  LLM sees: 5 matching jobs with scores.              │
│  LLM thinks: "I have results. Let me present them    │
│  to the user."                                       │
│  → Decides: TEXT RESPONSE (no more tool calls)       │
│  → Formats results as a readable summary             │
└──────────────────────┬──────────────────────────────┘
                       │ final response
                       ▼
┌─────────────────────────────────────────────────────┐
│                 DISPLAY TO USER                      │
│  "Here are 5 Python backend jobs I found: ..."       │
└─────────────────────────────────────────────────────┘
```

### The Loop in Pseudocode

```
function agent_run(user_message):
    add user_message to conversation history

    for iteration in 1..MAX_ITERATIONS:
        response = groq.chat(
            messages = conversation_history,
            tools    = tool_schemas,
            model    = "llama-3.3-70b-versatile"
        )

        message = response.choices[0].message

        if message has NO tool_calls:
            # LLM decided to respond with text — we're done
            add message.content to conversation history
            return message.content

        if message HAS tool_calls:
            # LLM wants to call one or more tools
            add message (with tool_calls) to conversation history

            for each tool_call in message.tool_calls:
                name = tool_call.function.name
                args = parse_json(tool_call.function.arguments)

                result = tool_registry.execute(name, args)

                add tool_result to conversation history
                # (role: "tool", tool_call_id: ..., content: result)

            # Loop continues — LLM sees tool results and reasons again

    return "Max iterations reached"
```

### What the Conversation History Looks Like

```json
[
  { "role": "system",    "content": "You are an AI Job Search Assistant..." },
  { "role": "user",      "content": "Find me Python backend jobs" },
  { "role": "assistant", "content": null, "tool_calls": [
      { "id": "call_1", "function": { "name": "get_job_stats", "arguments": "{}" } }
  ]},
  { "role": "tool", "tool_call_id": "call_1", "content": "{\"total_jobs\": 45}" },
  { "role": "assistant", "content": null, "tool_calls": [
      { "id": "call_2", "function": { "name": "search_jobs", "arguments": "{\"query\": \"python backend\", \"limit\": 5}" } }
  ]},
  { "role": "tool", "tool_call_id": "call_2", "content": "[{\"title\": \"Backend Engineer\"...}]" },
  { "role": "assistant", "content": "Here are 5 Python backend jobs I found: ..." }
]
```

> **NOTE:** The LLM sees the **entire conversation** on every call. This is how it "remembers" what tools it already called and what results it got. This is also why token management matters — long tool results eat context window.

---

## 4. Conversation Memory Architecture

### Short-term Memory (Phase 1)
- Just the conversation message list (as shown above)
- Grows per turn, reset between sessions
- Simple: list of dicts, no persistence

### Long-term Memory (Phase 2)
- **User preferences:** "I prefer remote jobs", "I'm targeting senior roles" → stored in a JSON file or SQLite
- **Search history:** what the user searched before, what they liked/rejected
- **Injected into system prompt** at the start of each session

### Token Management
- Tool results can be large (job descriptions). Options:
  - Summarize tool results before adding to history
  - Truncate old messages when approaching context limit
  - Only keep the last N turns in context

---

## 5. System Prompt Design

The system prompt is critical — it defines the agent's personality, capabilities, and decision-making guidelines.

Key sections:
1. **Identity:** what the agent is
2. **Available tools:** what it can do (auto-generated from registry)
3. **Decision guidelines:** when to use which tool
4. **Behavioral rules:** always check data before searching, explain reasoning, ask for clarification when ambiguous
5. **Output format:** how to present results to the user

Example guidelines for the agent:
```
- Before searching or matching, check if job data exists using get_job_stats
- If no data or user requests fresh data, use scrape_jobs first
- For broad exploration ("what jobs are out there"), use search_jobs
- For CV-specific matching ("what am I best suited for"), use match_all_jobs
- Only call tailor_cv after match_all_jobs has been run
- If a tool fails, explain the failure and suggest alternatives
- Never make up job listings — only present data from tools
```

---

## 6. Error Handling & Recovery

This is where a real agent differs from a script. The agent should **reason about failures** and try alternatives.

| Failure | Script Response | Agent Response |
|---|---|---|
| Qdrant unreachable | Crash with ConnectionError | "I can't reach the job database. Is Qdrant running? Start it with `docker compose up -d`" |
| No jobs in DB | Return empty list | "There are no jobs stored yet. Would you like me to scrape fresh listings from LinkedIn?" |
| Scraping blocked by LinkedIn | Crash or empty data | "LinkedIn blocked the scraping request. I can search existing data instead, or you can try again later." |
| Groq API rate limited | 429 error crash | "I've hit the API rate limit. Let me wait a moment and retry." (or use cached results) |
| Zero search results | Empty response | "No jobs matched 'quantum computing'. Want me to try broader terms like 'physics' or 'research engineer'?" |

The agent handles these because:
1. Tool execution is wrapped in try/except → returns error JSON instead of crashing
2. The LLM sees the error in the conversation → reasons about what to do next
3. The system prompt includes guidelines for handling common failures

---

## 7. Project Structure

```
project02(agentic)/
├── agent/
│   ├── __init__.py
│   ├── core.py              # The ReAct loop (Section 3)
│   ├── memory.py            # Conversation history management (Section 4)
│   └── prompts.py           # System prompt (Section 5)
├── tools/
│   ├── __init__.py
│   ├── registry.py          # Tool registration, schemas, execution engine
│   ├── scraper_tool.py      # Wraps P1: fetch_LinkedIn_jobs + ingest_jobs
│   ├── search_tool.py       # Wraps P1: embed_jobs.Search()
│   ├── match_tool.py        # Wraps P1: matching_engine.match_job()
│   ├── tailor_tool.py       # Wraps P1: groq_client.generate_tailored_recommendation()
│   └── data_tool.py         # Wraps P1: QdrantClient.get_collection()
├── config/
│   ├── __init__.py
│   └── settings.py          # Paths, env loading, P1 sys.path setup
├── cli.py                   # Terminal chat interface (entry point)
└── requirements.txt         # groq, python-dotenv (P1 deps via sys.path)
```

### How P2 Imports P1

P2 does **not** copy P1's code. It adds P1's root directory to `sys.path` at startup, then imports P1's modules directly:

```
config/settings.py:
    - Computes P1_ROOT = ../project01(storagevc)
    - Adds P1_ROOT to sys.path
    - Loads P1's .env file

tools/search_tool.py:
    - from embed_jobs import Search    ← imported from P1 via sys.path
    - Wraps Search() with error handling and return format
```

> **WARNING:** P1 modules use relative file paths (e.g., `open("cv_profile.json")`). Tool wrappers must either use absolute paths or temporarily change working directory to P1_ROOT before calling P1 functions.

---

## 8. Phased Implementation

### Phase 1: Core Agent Loop + Tools (This is where the learning happens)

**Goal:** A working CLI agent that can reason, call tools, and respond.

| Step | What | Learning Concept |
|---|---|---|
| 1 | `config/settings.py` — paths, env, P1 integration | Project structure, cross-project imports |
| 2 | Tool wrappers (5 files) — wrap P1 functions | How to expose capabilities as callable tools |
| 3 | `registry.py` — tool schemas + execution | Function calling format, tool registration pattern |
| 4 | `prompts.py` — system prompt | Prompt engineering for agent behavior |
| 5 | `memory.py` — conversation history | Message format, role-based history |
| 6 | `core.py` — the ReAct loop | **The core of agentic AI**: reasoning + acting in a loop |
| 7 | `cli.py` — terminal chat | User interaction loop |
| 8 | End-to-end testing | Verifying tool calling with Groq, debugging agent decisions |

**Done when:** You can chat with the agent in terminal, it calls the right tools, and returns useful results.

### Phase 2: Memory + Planning (Depth)

| Step | What | Learning Concept |
|---|---|---|
| 1 | Persistent memory — save user preferences to disk | Long-term memory, context injection |
| 2 | Planning step — agent breaks complex requests into sub-goals before acting | Goal decomposition, multi-step planning |
| 3 | Token management — summarize/truncate long tool results | Context window management |
| 4 | Retry logic — agent retries with different parameters on failure | Error recovery as reasoning |

**Done when:** Agent remembers your preferences across sessions and handles complex multi-step requests.

### Phase 3: Multi-Agent (Stretch)

| Step | What | Learning Concept |
|---|---|---|
| 1 | Split into specialist agents (Scraper, Analyst, Writer) | Agent specialization |
| 2 | Orchestrator agent delegates tasks | Multi-agent coordination |
| 3 | Agents communicate results via shared context | Inter-agent communication |

**Done when:** Multiple agents collaborate to handle a complex request.

---

## 9. What Each Phase Teaches You

| Concept | Phase | Industry Relevance |
|---|---|---|
| Tool use / Function calling | 1 | Core of every agent framework (LangChain, CrewAI, AutoGen) |
| ReAct loop | 1 | Standard agent architecture pattern |
| Prompt engineering for agents | 1 | How to guide agent behavior without code |
| Conversation memory | 1 | Stateful interactions |
| Persistent memory | 2 | Production agent systems |
| Goal decomposition / Planning | 2 | Complex task handling |
| Error recovery as reasoning | 2 | Robustness in production |
| Multi-agent coordination | 3 | Enterprise agent architectures |
| Agent evaluation | P3 | The hardest and most valuable skill |

---

## 10. Key Technical Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | None — built from scratch | Maximum learning; understand what frameworks abstract |
| LLM provider | Groq | Already integrated, fast, free tier, supports function calling |
| Agent model | Groq (llama-3.3-70b or equivalent with tool support) | Needs function calling capability |
| Interface | CLI first | Fastest to build, zero frontend overhead |
| P1 integration | sys.path import, not code copy | Minimal P1 changes, single source of truth |
| State management | In-memory dict shared between tools via closures | Simple, no external state store needed for Phase 1 |

---

## 11. Verification Plan

### Phase 1 Verification
1. **Tool isolation test:** Call each tool wrapper independently, verify it returns correct data
2. **Schema validation:** Verify Groq accepts the tool schemas without error
3. **Single-tool scenario:** "How many jobs are stored?" → agent should call `get_job_stats` and respond
4. **Multi-tool scenario:** "Find me Python jobs" → agent should call `get_job_stats` then `search_jobs`
5. **Failure scenario:** Stop Qdrant, ask for jobs → agent should handle the error gracefully
6. **Full flow:** "Match my CV and tailor for the best jobs" → agent chains `get_job_stats` → `match_all_jobs` → `tailor_cv`

### Prerequisites
- Qdrant running (Docker)
- P1's `.env` configured with Groq API key
- Jobs already in Qdrant (from P1 testing)
