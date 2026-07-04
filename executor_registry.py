import json
from pathlib import Path

from execution_context import ExecutionContext
from executors.codex_executor import CodexExecutor
from executors.gemini_executor import GeminiExecutor
from executors.mock import MockExecutor
from runtime_config import RuntimeConfig

DEFAULT_CONFIG_PATH = Path("config") / "executors.json"
SUPPORTED_TYPES = ("mock", "dry_run", "real", "cli")
MOCK_NAMES = ("mock", "mock_executor")


class ExecutorRegistryError(ValueError):
    pass


def boolean_setting(value, default=True):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("1", "true", "yes", "on"):
            return True
        if normalized in ("0", "false", "no", "off"):
            return False
    return bool(value)


class BlockedRealExecutor:
    def __init__(self, name, role, reason, policy):
        self.name = name
        self.role = role
        self.reason = reason
        self.policy = policy or {}

    def execute(self, task, context):
        task = task or {}
        execution_context = (context or {}).get("execution_context")
        task_id = task.get("id") or getattr(execution_context, "task_id", None) or (context or {}).get("task_id", "unknown")
        message = self.reason or "real executor execution is blocked in phase 3.1"
        output = f"Real executor blocked for {task_id}: {message}"
        if execution_context is not None:
            execution_context.update(executor_name=self.name, executor_role=self.role)
        return {
            "success": False,
            "executor": self.name,
            "role": self.role,
            "execution_id": getattr(execution_context, "execution_id", None),
            "output": output,
            "error": message,
            "blocked": True,
            "policy": self.policy,
        }


class ExecutorRegistry:
    def __init__(self, config_path=DEFAULT_CONFIG_PATH):
        self.config_path = Path(config_path)
        self.executors = {}
        self.errors = []

    def load(self):
        self.executors = {}
        self.errors = []
        try:
            raw = json.loads(self.config_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.errors.append(f"executor config not found: {self.config_path}")
            return self
        except json.JSONDecodeError as exc:
            self.errors.append(
                f"invalid executor config JSON: {exc.msg} at line {exc.lineno}, column {exc.colno}"
            )
            return self

        configured = raw.get("executors") if isinstance(raw, dict) else None
        if not isinstance(configured, dict):
            self.errors.append("executor config must contain an executors object")
            return self

        for name, config in configured.items():
            error = self._validate_entry(name, config)
            if error:
                self.errors.append(error)
                continue

            normalized = dict(config)
            normalized["name"] = name
            normalized["type"] = normalized.get("type", "mock")
            normalized["enabled"] = boolean_setting(normalized.get("enabled"), default=True)
            self.executors[name] = normalized
        return self

    def _validate_entry(self, name, config):
        if not isinstance(name, str) or not name.strip():
            return "executor name must be a non-empty string"
        if not isinstance(config, dict):
            return f"executor {name} must be an object"

        executor_type = config.get("type", "mock")
        if executor_type not in SUPPORTED_TYPES:
            return f"executor {name} has unsupported type: {executor_type}"

        role = config.get("role")
        if role is not None and (not isinstance(role, str) or not role.strip()):
            return f"executor {name} role must be a non-empty string"

        if executor_type in ("cli", "dry_run", "real"):
            command = config.get("command")
            if command is not None and (not isinstance(command, str) or not command.strip()):
                return f"executor {name} command must be a non-empty string"
        return None

    def resolve(self, name=None, role=None, task=None, runtime_config=None):
        task = task or {}
        selected = None
        reason = "fallback"
        fallback = False
        blocked = False

        if name:
            selected = self.executors.get(name)
            reason = "name"
        if selected is None and role:
            selected = self._find_by_role(role)
            reason = "role"

        if not self._is_usable(selected):
            selected = self._mock_config(role=role or task.get("role"), name=name)
            fallback = True
            reason = "fallback"

        kind = self._executor_kind(selected)
        runtime_config = runtime_config or RuntimeConfig()
        executor = self._build_executor(selected, task, runtime_config)

        if kind == "real":
            blocked = True
            policy = self._real_executor_policy(selected, runtime_config)
            if not policy["allowed"]:
                reason = "real-blocked"
                policy_reason = "real executor blocked by runtime policy"
            else:
                reason = "real-pending"
                policy_reason = "real executor resolution recorded; phase 3.1 does not launch real executors"
            executor = BlockedRealExecutor(
                name=selected.get("name", name or "real_executor"),
                role=selected.get("role") or role or task.get("role") or "real",
                reason=policy_reason,
                policy=policy,
            )
        else:
            policy = self._real_executor_policy(selected, runtime_config)

        return {
            "executor": executor,
            "config": selected,
            "fallback": fallback,
            "reason": reason,
            "blocked": blocked,
            "kind": kind,
            "policy": policy,
        }

    def _find_by_role(self, role):
        for config in self.executors.values():
            if config.get("role") == role:
                return config
        return None

    def _is_usable(self, config):
        if not config or not config.get("enabled", True):
            return False
        return config.get("type") in SUPPORTED_TYPES

    def _executor_kind(self, config):
        if not config:
            return "mock"
        executor_type = config.get("type", "mock")
        if executor_type == "cli":
            return "dry_run"
        return executor_type

    def _real_executor_policy(self, config, runtime_config):
        config = config or {}
        runtime_config = runtime_config or RuntimeConfig()
        name = config.get("name") or ""
        allowed = runtime_config.allows_real_executor(name)
        return {
            "name": name,
            "execution_mode": runtime_config.execution_mode,
            "enable_real_executors": runtime_config.enable_real_executors,
            "dry_run": runtime_config.dry_run,
            "allowed": allowed,
            "feature_flag_enabled": runtime_config.allows_real_executor(name),
        }

    def _mock_config(self, role=None, name=None):
        return {
            "name": "mock",
            "type": "mock",
            "role": role or "mock",
            "enabled": True,
            "fallback_for": name,
        }

    def _build_executor(self, config, task, runtime_config):
        kind = self._executor_kind(config)
        if kind == "dry_run":
            name = (config or {}).get("name", "")
            role = (config or {}).get("role") or task.get("role") or "dry_run"
            if "gemini" in name or role == "gemini":
                return GeminiExecutor(config, artifact_root=Path("artifacts"))
            if "codex" in name or role == "codex":
                return CodexExecutor(config, artifact_root=Path("artifacts"))
            return MockExecutor(
                role=task.get("role") or config.get("role") or "dry_run",
                should_succeed=mock_success_setting(task, config),
                output=task.get("mock_executor_output") or config.get("output") or "Dry-run executor prepared.",
                failure_reason=(
                    task.get("mock_executor_failure_reason")
                    or config.get("failure_reason")
                    or "Dry-run executor forced failure."
                ),
            )
        return MockExecutor(
            role=task.get("role") or config.get("role") or "mock",
            should_succeed=mock_success_setting(task, config),
            output=task.get("mock_executor_output") or config.get("output"),
            failure_reason=(
                task.get("mock_executor_failure_reason")
                or config.get("failure_reason")
            ),
        )


def mock_success_setting(task, config):
    for field in ("mock_executor_success", "mock_executor_should_succeed"):
        if field in task:
            return boolean_setting(task.get(field))
    if "should_succeed" in config:
        return boolean_setting(config.get("should_succeed"))
    return True


def load_executor_registry(config_path=DEFAULT_CONFIG_PATH):
    return ExecutorRegistry(config_path).load()
