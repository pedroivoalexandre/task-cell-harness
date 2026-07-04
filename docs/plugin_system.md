# Plugin System

`plugin_system.py` implements a controlled in-process registry. Plugins must be
registered manually, pass interface validation, and may be blocked unless they
are explicitly allowed. It does not auto-load external code.
