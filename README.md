# Task Cell Harness

Initial local harness for task orchestration experiments.

Current phase:
- FASE 4 is local, supervised, and audit-friendly.
- No external agents are executed automatically.
- Tasks move through the local filesystem.
- Logs are written as JSON Lines.
- Reports are generated in Markdown.

Planned flow:
1. Gemini implements.
2. Codex reviews.
3. Future arbiters may be added later.

Phase 4 boundary:
- real local use requires human approval;
- no Tablet integration is in scope;
- no distributed execution is in scope;
- no autonomous multi-agent dispatch is in scope;
- phase 5 is reserved for distributed execution;
- phase 6 is reserved for operations, observability, and stabilization.
