import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class RuntimeConfig:
    execution_mode: str = "dry_run"
    dry_run: bool = True
    enable_real_executors: bool = False
    default_timeout_seconds: int = 300
    retry_policy: dict = field(default_factory=lambda: {"max_retries": 0, "backoff_seconds": 0})
    max_parallel_tasks: int = 1
    artifact_retention_days: int = 30
    log_level: str = "INFO"
    feature_flags: dict = field(default_factory=dict)

    @classmethod
    def load(cls, path=None):
        config = cls()
        if path is None:
            return config
        path = Path(path)
        if not path.exists():
            return config
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("runtime config must be a JSON object")
        data = asdict(config)
        data.update(raw)
        loaded = cls(**{key: data[key] for key in data if key in cls.__dataclass_fields__})
        loaded.validate()
        return loaded

    def validate(self):
        if self.execution_mode not in ("dry_run", "real"):
            raise ValueError("execution_mode must be dry_run or real")
        if self.execution_mode == "real" and not self.enable_real_executors:
            raise ValueError("real execution is blocked unless enable_real_executors is true")
        if not self.enable_real_executors:
            self.dry_run = True
            self.execution_mode = "dry_run"
        if self.default_timeout_seconds <= 0:
            raise ValueError("default_timeout_seconds must be positive")
        if self.max_parallel_tasks <= 0:
            raise ValueError("max_parallel_tasks must be positive")
        if self.artifact_retention_days < 0:
            raise ValueError("artifact_retention_days must be non-negative")
        return True

    def allows_real_execution(self):
        return self.execution_mode == "real" and self.enable_real_executors and not self.dry_run

    def to_dict(self):
        return asdict(self)
