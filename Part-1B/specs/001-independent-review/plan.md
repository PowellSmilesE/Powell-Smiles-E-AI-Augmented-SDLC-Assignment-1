# Technical plan
- FastAPI POST /api/review and GET /health; self-contained UI.
- Groq JSON-object provider adapter behind injectable client.
- Pydantic strict data contract with source evidence alignment validation.
- Independent 25-case JSONL dataset, separate scoring module and full-run aggregator.
- Three harness layers: structural, source invariants, semantic. Six separate scoped gates.
- Genuine evidence pipeline: local pytest, Ruff, Bandit, live collector results, student gate review.
- Git incremental commits only for actual changes, never retroactively invented history.
