from .base import BaseExecutor


class MockExecutor(BaseExecutor):
    name = "mock"

    def __init__(self, role="mock", should_succeed=True, output=None, failure_reason=None):
        self.role = role
        self.should_succeed = should_succeed
        self.output = output
        self.failure_reason = failure_reason or "Mock executor forced failure."

    def execute(self, task, context):
        task_id = task.get("id") or context.get("task_id", "unknown")
        title = task.get("title") or ""
        if self.should_succeed:
            output = self.output or f"Mock execution completed for {task_id}: {title}"
            return {
                "success": True,
                "executor": self.name,
                "role": self.role,
                "output": output,
                "error": None,
            }

        output = self.output or f"Mock execution failed for {task_id}: {self.failure_reason}"
        return {
            "success": False,
            "executor": self.name,
            "role": self.role,
            "output": output,
            "error": self.failure_reason,
        }
