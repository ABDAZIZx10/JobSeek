# Portfolio Projects Plan

Three linked projects, one shared pipeline, three different skills demonstrated.

---

## Project 01: Job Data Engine (the toolbox) — ✅ COMPLETE

**Idea:** RAG system over scraped job postings + CV/profile, providing scraping, embedding, matching, and CV tailoring capabilities.

- **Scraper:** Python (Playwright + stealth) — pulls postings from LinkedIn (title, description, requirements, location, seniority)
- **Embedding + storage:** Qdrant vector DB with SentenceTransformer (384-dim cosine similarity)
- **Structured extraction:** Groq LLM extracts structured JobProfile / CandidateShape from raw text via JSON schema enforcement
- **Matching engine:** Multi-factor scoring — skills (35%), responsibilities (30%), experience (20%), seniority (15%) with dynamic weight redistribution
- **CV tailoring:** LLM-generated match reasons + tailored CV bullets for top matches
- **API:** FastAPI — `/scrape-and-embed`, `/matches`, `/match-cv` endpoints

**Design note:** Project 01 owns all scraping + embedding + matching logic. It becomes the **tool layer** that Project 02's agent calls — not a standalone product, but infrastructure.

---

## Project 02: Agentic Job Search Assistant (the AI agent)

**Idea:** A conversational AI agent that uses Project 01's capabilities as callable tools, making autonomous decisions about what to do based on user requests — not following a fixed script.

- **Agent loop:** ReAct cycle (Reason → Act → Observe → Reason again) built from scratch, no frameworks
- **Tool use:** P1's capabilities exposed as function-calling tools the agent invokes dynamically
- **Planning:** Agent decomposes complex goals into sub-steps and re-plans on failure
- **Memory:** Conversation context + persistent user preferences
- **Error recovery:** Agent reasons about failures and tries alternative approaches
- **Interface:** CLI chat (Phase 1), potential web UI later
- **LLM:** Groq (function calling API)

**Design note:** Project 02 never duplicates P1's logic — it wraps P1's functions as tools and lets the LLM decide which to call. The intelligence is in the reasoning loop, not the pipeline.

---

## Project 03: Agent Evaluation Harness (the QA layer)

**Idea:** A separate tool that tests whether Project 02's agent is actually making good decisions — not code correctness, but agent behavior quality.

- **Test set:** scripted scenarios with expected agent behaviors (e.g., "user asks for Python jobs → agent should search, not scrape fresh")
- **What it evaluates:**
  1. Tool selection quality — did the agent pick the right tools for the task?
  2. Reasoning quality — did the agent's chain-of-thought make sense?
  3. Recovery quality — did the agent handle failures gracefully?
  4. Output quality — are the final recommendations actually good?
  5. Regression tracking — compare agent behavior across prompt/model changes
- **Output:** a report (pass/fail per scenario, aggregate scores)

---

## Why this combination works

One real, deployed pipeline (Project 01) demonstrated through three distinct, in-demand skills:
- **RAG / data engineering** (P1) — already done
- **Agentic AI — tool use, reasoning loops, planning** (P2) — the core learning target
- **AI evaluation / agent QA** (P3) — the most undervalued skill on the job market

Niche angle: a localized job-market tool is distinctive versus generic RAG tutorial clones. The agent layer makes it genuinely interactive, not just a batch pipeline.