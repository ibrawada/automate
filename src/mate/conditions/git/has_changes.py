from pathlib import Path
import sys
import git

def run(cwd: Path, args: list[str] | None = None) -> bool:
    repo = git.Repo(cwd)
    # Returns True if there are unstaged changes, staged changes, or untracked files
    return repo.is_dirty(untracked_files=True)    



if __name__ == "__main__":
    print(f"input: {sys.argv[1:]}")
    has_changes = run(sys.argv[1])
    print(f"{sys.argv[1]} has changes: {has_changes}")
    sys.exit(0)