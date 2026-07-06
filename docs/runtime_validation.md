# Runtime Validation

`runtime_validation.py` performs pre-execution hardening checks before any real-agent work.

It also bootstraps the local runtime directories required for a clean-clone validation run,
so `python3 runner.py validate-runtime` can succeed without a manual `mkdir -p artifacts`.

## Checks

- Required directories.
- `config/executors.json` integrity.
- Runtime config safety and dry-run defaults.
- Basic filesystem permissions.
- Core project module presence.
- Explicit warnings when `config/runtime.json` is missing.

`python3 runner.py validate-runtime` writes `reports/runtime_validation.md` and stays in dry-run mode.
