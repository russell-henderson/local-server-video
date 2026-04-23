# GEMINI — Consolidated plan (short)

Last-updated: 2025-10-31

> Note: The LLM/search integration described here has been removed from the app; keep this document for historical reference only.

## Purpose

Provide a short, practical roadmap and immediate todos to evaluate and add a GEMINI-style LLM capability for non-critical automation: metadata enrichment and semantic search. This document is provider-agnostic and focuses on a small, testable rollout.

## Scope

- Metadata enrichment (title, description, tags)
- Embeddings for improved search relevance
- Admin-only assistant endpoints (no public chat initially)

## Success criteria

- Metadata suggestions (title, description, tags) are useful in manual review and improve discoverability
- Embeddings demonstrably improve manual relevance checks for search queries
- Prototype cost-per-video estimate and daily cost guardrails are available

## Top-level milestones (short)

1. Provider & cost evaluation (3-5 days): sample calls and cost spreadsheet
2. Metadata enrichment PoC (1 week): transcript -> generate title/description/tags -> compare suggestions
3. Embeddings & search PoC (1 week): small index + query tests
4. Admin endpoints & UI (1 week): trigger flows, preview results
5. Hardening & rollout (1-2 weeks): batching, caching, telemetry, tests

## Immediate actionable todos (this sprint)

1. Add config keys to `env.example`: `GEMINI_API_KEY`, `GEMINI_API_URL`, `GEMINI_PROVIDER`
2. Create `scripts/gemini_metadata_poc.py` (small script): read sample transcript, call model, write suggested metadata JSON
3. Write `docs/gemini-provider-eval.md` with example responses + cost estimates
4. Add prompt templates to `docs/gemini-prompts.md` (metadata + embeddings)

## Engineering notes

- Centralize API calls behind `ai_gateway.py` with a provider adapter (Gemini/OpenAI/Anthropic).
- Redact PII before sending; log minimal telemetry: latency, success/fail, token counts if available.
- Implement retry + exponential backoff (max 3 attempts) and per-call cost estimation.
- Unit tests: prompt formatting, metadata generation, embeddings handling, and mocked gateway integration.

## Prompt examples

- Metadata enrichment (concise):
   "From this transcript, suggest a title (<=80 chars), a description (<=300 chars), and 3-8 tags. Return JSON."

- Admin assistant (concise):
   "Given this video metadata and transcript, summarize quality issues and suggest fixes or action items in JSON."

## Privacy & cost guardrails

- Default: do not store raw audio longer than necessary; keep embeddings + metadata only.
- Add per-video cost estimate; block full LLM polish if estimated cost exceeds a configurable threshold.

## Next steps & owners

- Owner: assign an engineer to run provider evaluation and create `scripts/gemini_poc.py`.
- After PoC: decide embedding store (local FAISS vs managed) and add CI tests.

## References

- See `docs/OPENAI_COST_ANALYSIS.md` for cost background; merge key numbers into `docs/gemini-provider-eval.md`.

## Notes

This file is intentionally concise — use it as the canonical sprint plan for adding LLM capabilities. Expand into `docs/gemini-prompts.md` and `docs/gemini-provider-eval.md` as work progresses.
