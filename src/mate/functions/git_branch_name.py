from pathlib import Path
import subprocess


def run(cwd: Path) -> str:
    try:
        # Get current branch
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd, text=True, stderr=subprocess.DEVNULL
        ).strip()

        return branch

    except (subprocess.CalledProcessError, IndexError):
        # This can happen if 'origin' remote doesn't exist or URL is malformed
        return None