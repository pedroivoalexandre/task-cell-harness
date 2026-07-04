# Runtime Validation

`runtime_validation.py` checks required directories, executor config, runtime
configuration, dry-run safety, and basic project integrity. The runner exposes it
through `python3 runner.py validate-runtime`, which writes
`reports/runtime_validation.md` without modifying tasks or executing agents.
