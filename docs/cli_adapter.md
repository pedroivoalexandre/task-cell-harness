# CLI Adapter

`executors/cli_adapter.py` defines the dry-run CLI integration base. It prepares
future command metadata without executing external processes.

`CLIAdapter` responsibilities:

- validate configuration
- build command arrays
- validate environment metadata
- perform dry-run planning
- prepare stdin/stdout/stderr structures

No subprocess is started by this adapter.
