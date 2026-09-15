from pathlib import Path
import sys
import git

from mate import output
from . import git_utils

# def run(cwd: Path, args: list[str] | None = None) -> bool:
#     is_repo = git_utils.is_git_repo(cwd)

#     if is_repo:
#         repo = git.Repo(cwd)
#         # Returns True if there are unstaged changes, staged changes, or untracked files
#         branches = repo.branches
        
#         return repo.is_dirty(untracked_files=True)
#     else:
#         output.warning(f"Current directory is not a repository: {cwd}")
#         return False



# if __name__ == "__main__":
#     print(f"input: {sys.argv[1:]}")
#     has_changes = run(sys.argv[1])
#     print(f"{sys.argv[1]} has changes: {has_changes}")
#     sys.exit(0)