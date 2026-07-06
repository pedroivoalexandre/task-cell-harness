from dataclasses import asdict, dataclass, field
from pathlib import Path
import json


@dataclass
class TaskCell:
    task_id: str
    title: str
    objective: str
    context: str
    inputs: list = field(default_factory=list)
    constraints: list = field(default_factory=list)
    allowed_actions: list = field(default_factory=list)
    forbidden_actions: list = field(default_factory=list)
    acceptance_criteria: list = field(default_factory=list)
    expected_artifacts: list = field(default_factory=list)
    implementer_prompt: str = ""
    reviewer_prompt: str = ""
    status: str = "draft"
    report: str = ""

    @classmethod
    def from_dict(cls, data):
        return cls(**{field.name: data.get(field.name) for field in cls.__dataclass_fields__.values()})

    def to_dict(self):
        return asdict(self)

    @classmethod
    def load(cls, path):
        path = Path(path)
        return cls.from_dict(json.loads(path.read_text(encoding="utf-8")))

    def dump(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return path
