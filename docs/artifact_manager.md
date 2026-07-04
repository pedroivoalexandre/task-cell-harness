# Artifact Manager

`artifact_manager.py` is the official artifact registry for the harness. It
stores execution artifacts under:

```text
artifacts/<task_id>/<execution_id>/
```

Each execution directory contains an `artifacts.json` index. Every entry records:

- `artifact_id`
- `task_id`
- `execution_id`
- `name`
- `path`
- `kind`
- `created_at`
- `size_bytes`
- `checksum_sha256`

The runner registers generated Markdown reports as `markdown_report` artifacts
when an `ExecutionContext` exists. The manager copies the source file into the
execution artifact directory and updates the context `log_context` with the
index path.
