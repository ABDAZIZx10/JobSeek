# Hybrid Search Deep Dive (Project 01)

This is a refresher of **how this repo stores jobs in Qdrant and retrieves them**. It follows the actual code, not a generic RAG tutorial.

Two retrieval paths exist. Only one of them is hybrid search.

| Path | Entry | Ranking | Used by |
|---|---|---|---|
| **Hybrid search** | `embed_jobs.Search()` | Dense similarity + BM25 sparse + RRF | P2 `search_jobs` |
| **CV matching** | `match_cv_tailor` / P2 `match_all_jobs` | Scroll **all** points, score with `match_job` weights | P2 `match_all_jobs` |

CV matching does **not** embed the CV or query Qdrant by vector. It walks the collection with `scroll` and compares structured profiles. This document is about the hybrid path, plus the collection layout both paths share.

---

## 1. Mental model

A job is not stored as “the LinkedIn HTML.” Ingest splits it into three layers:

```
raw LinkedIn job
        │
        ▼
   Groq JobProfile          ← structured: skills, seniority, tech, responsibilities
        │
        ├── job_text        → dense vector  (BGE, 384 dims, cosine)
        ├── sparse_text     → sparse vector (BM25 token weights)
        └── payload         → JSON Qdrant stores beside the vectors
```

**Vectors** answer: “which jobs *feel* like this query?”  
**Payload filters** answer: “which jobs *must* be junior / London / remote?”  
**Hybrid** means two vector searches (dense + sparse) whose ranked lists are merged with **RRF**.

Hard filters run as a **gate**. If the gate removes every point, hybrid never gets a chance. That is why `"junior python software dev"` can return 0 jobs even when Python jobs exist.

---

## 2. The collection

Created in `qDrantStore.connect()` if missing.

```python
vectors_config={
    "dense": VectorParams(size=384, distance=Distance.COSINE)
},
sparse_vectors_config={
    "sparse": SparseVectorParams(index=SparseIndexParams(on_disk=False))
}
```

Named vectors on **one** point:

- `dense` — 384 floats. Size matches `BAAI/bge-small-en-v1.5`.
- `sparse` — map of `{token_id: weight}` from FastEmbed `Qdrant/bm25`.

Each point also has a payload:

```python
{
  "profile":    { ... JobProfile ... },   # structured extract
  "raw_job":    { ... scraped LinkedIn ... },
  "job_filters": { ... JobFilters ... }   # hard constraints for payload filter
}
```

`storeVector` upserts with a random UUID. Same job scraped twice = two points (no dedupe).

Full-text payload indexes exist on `job_filters.location` and `job_filters.seniority` so `MatchText` is case-insensitive.

---

## 3. Dense embeddings (BGE)

`model_provider.get_model()` loads **`BAAI/bge-small-en-v1.5`** once (module-level singleton). That model maps English text → a 384-dimensional vector.

### Cosine similarity (what Qdrant uses)

Two vectors \(\mathbf{a}, \mathbf{b}\):

\[
\cos(\mathbf{a},\mathbf{b}) = \frac{\mathbf{a}\cdot\mathbf{b}}{\|\mathbf{a}\|\,\|\mathbf{b}\|}
\]

Range is roughly \([-1, 1]\). Near **1** = similar direction = similar meaning. Qdrant ranks by this for the `dense` named vector.

Dense search is **semantic**. “backend engineer” can match “server-side software developer” even if the words differ. It is weak at exact tokens (`C++`, error codes, rare library names) unless those strings appeared in similar contexts during training.

### Query prefix (asymmetric retrieval)

BGE was trained with a search prefix on the **query**, not on documents.

```python
def embed_job(job_text, model, is_query=False):
    if is_query:
        job_text = "Represent this sentence for searching relevant passages: " + job_text
    return model.encode(job_text)
```

- **Ingest:** `embed_job(job_text, model)` — no prefix.  
- **Search:** `embed_job(query, model, is_query=True)` — prefix added.

Using the prefix on stored jobs (or skipping it on queries) silently hurts ranking. The two sides of the comparison must stay asymmetric the way the model was trained.

### What text gets embedded at ingest

`build_job_text` does **not** embed the full LinkedIn description. It builds a compact card from title/company/location plus Groq profile fields:

```
Title: ...
Company: ...
Location: ...
Role Aliases: ...
Technologies: ...
Experience Years: ...
Seniority: ...
```

That is a design choice: the dense vector is biased toward **role + stack + seniority**, not the long duties paragraph. Duties live in payload `profile.responsibilities` and in sparse text (below).

---

## 4. Sparse embeddings (BM25)

`get_sparse_model()` uses FastEmbed:

```python
SparseTextEmbedding(model_name="Qdrant/bm25")
```

BM25 is **lexical**, not semantic. It scores how important each term is in a document relative to the collection (term frequency × inverse document frequency, with length normalization). The output is a **sparse** vector: most dimensions are 0; only tokens that appear get a weight.

```python
def sparse_embedding(sparse_model, job_text):
    vector = list(sparse_model.embed([job_text]))[0]
    return SparseVector(
        indices=vector.indices.tolist(),
        values=vector.values.tolist()
    )
```

- `indices` — which token IDs fired  
- `values` — BM25 weights for those tokens  

Sparse search shines when the user types a **specific string** (`FastAPI`, `Kubernetes`, `Visa`). Dense search might still rank a “Python web” job highly; BM25 boosts jobs that actually contain the token.

At ingest, sparse text is **richer** than dense text: title, technologies, role aliases, **and** the job description. Query-time sparse embedding uses the raw user query (no BGE prefix).

---

## 5. Why hybrid (dense + sparse)

| | Dense (BGE) | Sparse (BM25) |
|---|---|---|
| Strength | Paraphrase / intent | Exact keywords |
| Weakness | Misses rare tokens | Misses synonyms |
| This repo | Role/stack card | Title + tech + description |

A query like `"python backend k8s"` needs both: “backend” as meaning, `k8s` as a token. Hybrid runs **two candidate lists**, then fuses them.

---

## 6. Reciprocal Rank Fusion (RRF)

`SearchVector` does not average cosine and BM25 scores (those scales are not comparable). It uses Qdrant `Fusion.RRF`.

**Prefetch** (retrieve separately):

```python
prefetch=[
    Prefetch(query=dense_vector,  using="dense",  limit=20),
    Prefetch(query=sparse_vector, using="sparse", limit=20),
]
query=FusionQuery(fusion=Fusion.RRF)
limit=limit   # final K, e.g. 5
```

Each prefetch keeps its top 20. RRF then scores a point by **rank** in each list:

\[
\mathrm{RRF}(d) = \sum_{r \in \text{rankers}} \frac{1}{k + \mathrm{rank}_r(d)}
\]

Typical \(k = 60\). Rank 1 contributes \(1/61\); rank 10 contributes \(1/70\). Appearing in **both** lists beats appearing first in only one. The final `limit` is applied **after** fusion.

The `score` P2 shows on a search hit is this fused score, not raw cosine.

---

## 7. Hard filters (payload), not vectors

Before / around the vector query, Groq turns the user string into `JobFilters`:

```python
class JobFilters(BaseModel):
    location: Optional[str]
    remote: Optional[bool]
    seniority: Optional[str]
    min_salary, max_salary: Optional[int]
    visa_sponsorship, clearance_required: Optional[bool]
    max_age_days: Optional[int]
```

`build_qdrant_filter` turns non-null fields into `Filter(must=[...])`. **Every** `must` clause must match. Skills and job titles are **not** filters; they belong in the semantic/sparse query.

Examples:

- `"junior python in London"` → Groq may set `seniority=junior`, `location=London`. Vectors only see the remaining intent (`python`). If stored `job_filters.seniority` is `"entry level"` or missing, **0 results**.
- `"python developer"` with no explicit seniority → `active_filters` empty → `query_filter=None` → hybrid over the whole collection.

This is the most common “search is broken” failure in this project. Check the printed `filters: {...}` line. Empty hybrid + a `must` filter almost always means the **gate**, not BGE.

---

## 8. End-to-end: ingest

`ingest_jobs` (called from the scrape pipeline):

1. `connect()` — ensure collection + text indexes.  
2. For each scraped job:
   - Groq `generate_job_description` → `JobProfile` (skills, tech, seniority enum, responsibilities, role aliases).  
   - `build_job_text` → dense embedding (no query prefix).  
   - Groq `extract_job_filters` on the **job** → payload `job_filters`.  
   - Sparse embedding on title + tech + roles + description.  
   - `storeVector(..., vector={"dense": ..., "sparse": ...}, job=payload)`.  
3. Sleep 30s after the last job to stay under Groq TPM.

Ingest quality = search quality. If Groq leaves `seniority` null, later `must` filters on junior/senior will drop that point.

---

## 9. End-to-end: search

`Search(query, limit)`:

1. Groq `extract_job_filters(query)` → print active filters → `build_qdrant_filter`.  
2. Dense query vector **with** BGE prefix.  
3. Sparse query vector from the same query string.  
4. `SearchVector` → prefetch 20+20 → RRF → top `limit`.  
5. Map payload `raw_job` to `{title, company, location, url, score, details}`.

P2 `search_jobs` is a thin wrapper that drops `details` for the agent.

```
user query
    │
    ├─► Groq filters ──► Qdrant must-filter (hard gate)
    ├─► BGE + prefix ──► prefetch dense top 20
    └─► BM25 ──────────► prefetch sparse top 20
                              │
                              ▼
                         RRF fusion
                              │
                              ▼
                         top K jobs
```

---

## 10. How this differs from CV matching

`match_all_jobs` / `match_cv_tailor`:

- No `embed_job`, no BM25, no RRF.  
- `scroll` pages of 60 points, payload only.  
- `match_job` weights: skills 35, responsibilities 30, experience 20, seniority 15 (weights drop to 0 if a side is missing).  
- Rank by `final_score`.

So: **search** = “jobs like this sentence.” **Match** = “jobs whose structured profile fits this CV,” over the whole collection. A job can be a great hybrid hit and a poor CV match (or the reverse).

---

## 11. Implementation notes (useful when debugging)

- **`HOST` / `PORT`:** `connect()` uses `http://{HOST}:{PORT}`. Docker must set `HOST=qdrant_database` (service name), not `127.0.0.1`.  
- **`COLLECTION_NAME`:** must match ingest and search.  
- **Sparse model:** `get_sparse_model()` builds a new `SparseTextEmbedding` every call (dense model is cached). Harmless, slightly wasteful.  
- **No job deduplication** on upsert.  
- **Prefetch 20 / final 5:** if both lists miss a relevant job, RRF cannot recover it. Raising prefetch is the knob, not `limit` alone.  
- **Filter vs intent:** put seniority/location in filters only when the user stated them as constraints; put stack/role in the query text.

---

## 12. Quick self-check

Without opening files, you should be able to answer:

1. Why is dense size **384**?  
2. Why does search add a **prefix** that ingest does not?  
3. Why fuse with **RRF** instead of averaging scores?  
4. Why can hybrid return **0** when the collection is not empty?  
5. Does matching a CV use these vectors?  

Answers: (1) BGE-small output dim. (2) BGE asymmetric query prefix. (3) Cosine and BM25 are not on the same scale; ranks are. (4) `Filter(must=...)` dropped everything. (5) No — scroll + `match_job`.

---

## Code map

| File | Role |
|---|---|
| `model_provider.py` | BGE singleton, BM25 FastEmbed |
| `embed_jobs.py` | `build_job_text`, `embed_job`, `sparse_embedding`, `ingest_jobs`, `Search` |
| `qDrantStore.py` | `connect`, collection schema, `storeVector`, `build_qdrant_filter`, `SearchVector` |
| `models/JobProfile.py` | Structured job extract (dense/sparse source + match payload) |
| `models/jobfilters.py` | Hard-filter schema |
| `groq_client.py` | `generate_job_description`, `extract_job_filters` |
| `project02/tools/search_tool.py` | Agent wrapper around `Search` |
