from pathlib import Path
from git import Repo, InvalidGitRepositoryError

def is_git_repo(dir: Path):
    try:
        # search_parent_directories=True checks if the path is inside a repo
        repo = Repo(dir, search_parent_directories=True)
        return True
    except InvalidGitRepositoryError:
        return False