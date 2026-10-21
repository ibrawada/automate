import pytest

from .helpers import git, read_toml, strip_ansi


pytestmark = pytest.mark.smoke


def test_help(run_mate_subprocess):
    result = run_mate_subprocess("--help")

    assert result.code == 0
    assert "usage:" in strip_ansi(result.out)


def test_config_roundtrip(run_mate_subprocess, workspace, global_config):
    assert run_mate_subprocess("config", "vars:name=smoke").code == 0

    result = run_mate_subprocess("config", "--show")

    assert result.code == 0
    assert "vars:name = smoke" in strip_ansi(result.out).splitlines()
    assert global_config.exists()
    assert read_toml(workspace.local_config)["vars"]["name"] == "smoke"


def test_shell_command_with_placeholder(run_mate_subprocess, workspace):
    result = run_mate_subprocess("mkdir", "%folder_name[]%_dir")

    assert result.code == 0
    assert result.report == {name: 0 for name in workspace.folders}
    for folder in workspace.paths():
        assert (folder / f"{folder.name}_dir").is_dir()


@pytest.mark.git
def test_git_init_and_commit(run_mate_subprocess, git_workspace):
    run_mate_subprocess("git", "init")
    git_workspace.write("file.txt", "content")
    run_mate_subprocess("git", "add", ".")

    result = run_mate_subprocess("git", "commit", "-m", "smoke %folder_name[]%")

    assert result.report == {name: 0 for name in git_workspace.folders}
    for folder in git_workspace.paths():
        assert git(folder, "log", "--format=%s") == f"smoke {folder.name}"
