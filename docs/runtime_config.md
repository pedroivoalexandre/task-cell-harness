# Runtime Configuration

`runtime_config.py` provides safe runtime defaults. Execution starts in `dry_run`,
`enable_real_executors` defaults to `false`, and real execution is rejected unless
explicitly enabled. Configuration can be loaded from JSON while preserving safe
defaults.
