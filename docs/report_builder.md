# Report Builder

`report_builder.py` centralizes task report generation. It produces both
Markdown and JSON representations while preserving the existing Markdown report
shape used by earlier harness tasks.

Inputs consolidated by `ReportBuilder`:

- `ExecutionContext`
- artifacts
- logs
- review result
- task id, title, and status

The runner uses `ReportBuilder` for review reports and keeps execution fully
simulated.
