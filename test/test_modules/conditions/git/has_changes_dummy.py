from pathlib import Path


def run(cwd: Path, args: list[str] | None = None) -> bool:
    if args:
        return True
    return False


