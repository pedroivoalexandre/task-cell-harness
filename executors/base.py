from abc import ABC, abstractmethod


class BaseExecutor(ABC):
    name = "base"
    role = "executor"

    @abstractmethod
    def execute(self, task, context):
        """Execute a task and return a result dictionary."""
        raise NotImplementedError
