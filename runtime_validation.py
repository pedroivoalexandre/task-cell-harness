import os
from pathlib import Path

from executor_registry import load_executor_registry
from runtime_config import RuntimeConfig

REQUIRED_DIRS = ("tasks", "reports", "logs", "artifacts", "config", "docs", "executors")
REQUIRED_MODULES = (
    "runner.py",
    "runtime_config.py",
    "event_bus.py",
    "metrics_collector.py",
    "resource_manager.py",
    "plugin_system.py",
    "runtime_validation.py",
    "execution_context.py",
    "executor_registry.py",
    "artifact_manager.py",
    "report_builder.py",
    "prompt_builder.py",
    "state_machine.py",
    "scheduler.py",
    "executors/base.py",
    "executors/mock.py",
    "executors/cli_adapter.py",
    "executors/gemini_executor.py",
    "executors/codex_executor.py",
)


class RuntimeValidator:
    def __init__(self, root=Path(".")):
        self.root = Path(root)

    def validate(self):
        checks = []
        warnings = []
        checks.extend(self._check_directories())
        checks.append(self._check_executor_config())
        runtime_check = self._check_runtime_config()
        checks.append(runtime_check)
        warnings.extend(runtime_check.get("warnings", []))
        checks.append(self._check_dry_run_safety())
        checks.append(self._check_permissions())
        checks.append(self._check_project_integrity())
        ok = all(check["ok"] for check in checks)
        return {"ok": ok, "checks": checks, "warnings": warnings}

    def write_report(self, path):
        result = self.validate()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# Runtime Validation", "", f"Result: {'OK' if result['ok'] else 'FAILED'}", ""]
        for warning in result.get("warnings", []):
            lines.append(f"- Warning: {warning}")
        if result.get("warnings"):
            lines.append("")
        for check in result["checks"]:
            status = "OK" if check["ok"] else "FAILED"
            lines.append(f"- {check['name']}: {status} - {check['message']}")
        path.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
        return result

    def _check_directories(self):
        return [
            {
                "name": f"directory:{directory}",
                "ok": (self.root / directory).exists(),
                "message": str(self.root / directory),
            }
            for directory in REQUIRED_DIRS
        ]

    def _check_executor_config(self):
        registry = load_executor_registry(self.root / "config" / "executors.json")
        return {
            "name": "config/executors.json",
            "ok": not registry.errors,
            "message": "; ".join(registry.errors) if registry.errors else "valid",
        }

    def _check_runtime_config(self):
        config_path = self.root / "config" / "runtime.json"
        try:
            config, warnings = RuntimeConfig.load_with_warnings(config_path)
            safe_defaults = not config.allows_real_execution()
            message = "safe defaults valid" if safe_defaults else "real execution enabled"
            return {
                "name": "runtime_config",
                "ok": safe_defaults,
                "message": message,
                "warnings": warnings,
            }
        except Exception as exc:
            return {"name": "runtime_config", "ok": False, "message": str(exc), "warnings": []}

    def _check_dry_run_safety(self):
        config = RuntimeConfig.load(self.root / "config" / "runtime.json")
        return {
            "name": "dry_run_safety",
            "ok": not config.allows_real_execution(),
            "message": "real executors blocked" if not config.allows_real_execution() else "real execution enabled",
        }

    def _check_permissions(self):
        executors = self.root / "config" / "executors.json"
        return {
            "name": "permissions",
            "ok": (
                os.access(self.root, os.R_OK | os.W_OK | os.X_OK)
                and executors.exists()
                and os.access(executors, os.R_OK)
                and os.access(self.root / "reports", os.R_OK | os.W_OK | os.X_OK)
            ),
            "message": "project root and config/report paths are readable and writable",
        }

    def _check_project_integrity(self):
        missing = [name for name in REQUIRED_MODULES if not (self.root / name).exists()]
        return {
            "name": "project_integrity",
            "ok": not missing,
            "message": "missing: " + ", ".join(missing) if missing else "required modules present",
        }
