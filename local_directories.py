from pathlib import Path

LOCAL_DIRECTORIES = (
    "artifacts",
    "logs",
    "logs/errors",
    "logs/tasks",
    "reports",
    "runtime/locks",
    "runtime/state",
    "runtime/temp",
)


def ensure_local_directories(root=Path(".")):
    root = Path(root)
    created = []
    for relative_path in LOCAL_DIRECTORIES:
        directory = root / relative_path
        directory.mkdir(parents=True, exist_ok=True)
        created.append(directory)
    return created
