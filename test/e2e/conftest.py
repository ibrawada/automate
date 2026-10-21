import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

from mate import globals
from mate import main as mate_main

from .helpers import Result, git, parse_report


SRC_DIR = Path(__file__).resolve().parents[2] / "src"

# Folders created in every test workspace. "build" is excluded by the default local config.
PROJECT_FOLDERS = ["alpha", "beta", "gamma"]
EXCLUDED_FOLDERS = ["build"]


def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.e2e)


@dataclass
class Workspace:
    root: Path
    folders: list[str]

    def path(self, name: str) -> Path:
        return self.root / name

    def paths(self) -> list[Path]:
        return [self.path(name) for name in self.folders]

    def write(self, relative_path: str, content: str):
        """Writes the same file into every project folder."""
        for folder in self.paths():
            (folder / relative_path).write_text(content, encoding="utf-8")

    @property
    def local_config(self) -> Path:
        return self.root / ".mate" / globals.LOCAL_CONFIG_FILE_NAME


@pytest.fixture(autouse=True)
def fake_home(tmp_path, monkeypatch) -> Path:
    """Redirects the global config (~/.mate/mate-global.toml) into the test's temp dir."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    # Keep the process working directory stable: some commands resolve paths relative to it
    monkeypatch.chdir(tmp_path)
    yield home
    globals.set_workspace_dir(Path("."))


@pytest.fixture
def global_config(fake_home) -> Path:
    return fake_home / ".mate" / globals.GLOBAL_CONFIG_FILE_NAME


@pytest.fixture
def workspace(tmp_path) -> Workspace:
    root = tmp_path / "ws"
    for name in PROJECT_FOLDERS + EXCLUDED_FOLDERS:
        (root / name).mkdir(parents=True)
    return Workspace(root=root, folders=list(PROJECT_FOLDERS))


@pytest.fixture
def run_mate(workspace, capfd):
    """Runs mate in-process against the test workspace and captures stdout/stderr on fd level
    (so output of child processes like git or the shell is included)."""

    def _run(*args: str) -> Result:
        capfd.readouterr()  # drop output of previous calls
        try:
            code = mate_main.main(["--wsd", str(workspace.root), *args])
        except SystemExit as e:
            code = e.code
        captured = capfd.readouterr()
        return Result(code=code, out=captured.out, err=captured.err, report=parse_report(captured.out))

    return _run


@pytest.fixture
def run_mate_subprocess(workspace):
    """Runs mate as a real process via `python -m mate`. Arguments are passed as a list,
    so no shell expands the %...% placeholders."""

    def _run(*args: str, timeout: float = 60) -> Result:
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(SRC_DIR), env.get("PYTHONPATH")]))
        completed = subprocess.run(
            [sys.executable, "-m", "mate", "--wsd", str(workspace.root), *args],
            capture_output=True, text=True, env=env, timeout=timeout,
        )
        return Result(code=completed.returncode, out=completed.stdout, err=completed.stderr,
                      report=parse_report(completed.stdout))

    return _run


@pytest.fixture
def mate_initialized(run_mate, workspace, global_config):
    """Any mate invocation creates the global and local config files."""
    run_mate("config", "--show")
    assert global_config.exists() and workspace.local_config.exists()
    return run_mate


@pytest.fixture
def git_env(tmp_path, monkeypatch):
    """Isolates git from the user's/system git configuration."""
    if shutil.which("git") is None:
        pytest.skip("git is not installed")

    gitconfig = tmp_path / "gitconfig"
    gitconfig.write_text(
        "[user]\n\tname = Mate Test\n\temail = mate@test.invalid\n"
        "[init]\n\tdefaultBranch = main\n"
        "[commit]\n\tgpgsign = false\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", str(gitconfig))
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    for var in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.delenv(var, raising=False)
    return gitconfig


@pytest.fixture
def git_workspace(workspace, git_env) -> Workspace:
    return workspace


@pytest.fixture
def git_repos(git_workspace) -> Workspace:
    """Every project folder is a git repo with one initial commit."""
    for folder in git_workspace.paths():
        git(folder, "init")
        (folder / "README.md").write_text(f"# {folder.name}\n", encoding="utf-8")
        git(folder, "add", ".")
        git(folder, "commit", "-m", "initial")
    return git_workspace
