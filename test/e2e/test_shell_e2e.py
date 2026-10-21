import shutil
import sys

import pytest

from .helpers import strip_ansi


IS_WINDOWS = sys.platform.startswith("win")


def test_mkdir_in_every_project_folder(run_mate, workspace):
    result = run_mate("mkdir", "sub")

    assert result.report == {name: 0 for name in workspace.folders}
    for folder in workspace.paths():
        assert (folder / "sub").is_dir()
    assert not (workspace.path("build") / "sub").exists()


def test_mkdir_with_whitespace_in_name(run_mate, workspace):
    result = run_mate("mkdir", "dir with space")

    assert result.report == {name: 0 for name in workspace.folders}
    for folder in workspace.paths():
        assert (folder / "dir with space").is_dir()


def test_mkdir_with_function_placeholder(run_mate, workspace):
    run_mate("mkdir", "%folder_name[]%_out")

    for folder in workspace.paths():
        assert (folder / f"{folder.name}_out").is_dir()


def test_mkdir_with_config_placeholder(run_mate, workspace):
    run_mate("config", "vars:dir=generated")

    run_mate("mkdir", "%vars:dir%")

    for folder in workspace.paths():
        assert (folder / "generated").is_dir()


def test_mkdir_only_selected_folders(run_mate, workspace):
    run_mate("mkdir", "sub", "--only=beta")

    assert (workspace.path("beta") / "sub").is_dir()
    assert not (workspace.path("alpha") / "sub").exists()
    assert not (workspace.path("gamma") / "sub").exists()


def test_shell_exit_code_is_reported(run_mate, workspace):
    result = run_mate("exit", "3")

    assert result.report == {name: 3 for name in workspace.folders}
    assert "To retry" in strip_ansi(result.out)


@pytest.mark.skipif(not IS_WINDOWS, reason="PowerShell is the default shell on Windows only")
def test_default_shell_is_powershell(run_mate, workspace):
    # Set-Content is a PowerShell cmdlet, it does not exist in cmd
    result = run_mate("Set-Content", "-Path", "out.txt", "-Value", "%folder_name[]%")

    assert result.report == {name: 0 for name in workspace.folders}
    for folder in workspace.paths():
        assert (folder / "out.txt").read_text().strip() == folder.name


@pytest.mark.skipif(not IS_WINDOWS, reason="cmd is only available on Windows")
def test_shell_configured_as_cmd(run_mate, workspace):
    run_mate("config", "shell:windows=cmd")

    # "ver" is a cmd builtin which is not available in PowerShell
    result = run_mate("ver", ">", "ver.txt")

    assert result.report == {name: 0 for name in workspace.folders}
    for folder in workspace.paths():
        assert "Windows" in (folder / "ver.txt").read_text()


@pytest.mark.skipif(IS_WINDOWS or shutil.which("sh") is None, reason="POSIX shell only")
def test_shell_configured_as_sh(run_mate, workspace):
    run_mate("config", "shell:linux=sh", "shell:macos=sh")

    # "cd" is a shell builtin, so mate falls back to the configured shell
    result = run_mate("cd", ".", "&&", "pwd", ">", "pwd.txt")

    assert result.report == {name: 0 for name in workspace.folders}
    for folder in workspace.paths():
        assert (folder / "pwd.txt").read_text().strip().endswith(folder.name)


def test_unknown_shell_exits_with_error(run_mate, workspace):
    run_mate("config", "shell:windows=no-such-shell", "shell:linux=no-such-shell", "shell:macos=no-such-shell")

    result = run_mate("exit", "0")

    assert result.code == 127
    assert "Shell application not found" in strip_ansi(result.out)
