import json
import sys

import pytest

from mate import globals

from .helpers import strip_ansi


RECORDER_SCRIPT = """\
import json, sys
from pathlib import Path
Path("recorded.json").write_text(json.dumps({"cwd": Path.cwd().name, "argv": sys.argv[1:]}))
sys.exit(int(Path("exit_code.txt").read_text()) if Path("exit_code.txt").exists() else 0)
"""


@pytest.fixture
def recorder(run_mate, tmp_path):
    """Registers the python interpreter as config executable "rec" and returns the recorder script,
    which writes its working directory and arguments into recorded.json."""
    script = tmp_path / "recorder.py"
    script.write_text(RECORDER_SCRIPT, encoding="utf-8")
    run_mate("config", "-g", f"executables:rec={sys.executable}")
    return script


def recorded(folder) -> dict:
    return json.loads((folder / "recorded.json").read_text())


def test_config_executable_runs_in_every_folder(run_mate, workspace, recorder):
    result = run_mate("rec", str(recorder), "file.txt")

    assert result.report == {name: 0 for name in workspace.folders}
    for folder in workspace.paths():
        assert recorded(folder) == {"cwd": folder.name, "argv": ["file.txt"]}
    assert not (workspace.path("build") / "recorded.json").exists()


def test_config_executable_with_placeholders(run_mate, workspace, recorder):
    run_mate("config", "vars:ext=.txt")

    # Only one placeholder per argument is supported
    run_mate("rec", str(recorder), "%folder_name[]%.txt", "%vars:ext%")

    for folder in workspace.paths():
        assert recorded(folder)["argv"] == [f"{folder.name}.txt", ".txt"]


def test_config_executable_exit_code_is_reported(run_mate, workspace, recorder):
    (workspace.path("beta") / "exit_code.txt").write_text("5")

    result = run_mate("rec", str(recorder))

    assert result.report == {"alpha": 0, "beta": 5, "gamma": 0}


def test_missing_config_executable_is_reported(run_mate, workspace):
    run_mate("config", "-g", "executables:npp=C:/does/not/exist/notepad++.exe")

    result = run_mate("npp", "readme.txt")

    assert result.report == {name: globals.ERROR_CODE for name in workspace.folders}
    assert "command not found" in strip_ansi(result.out)


def test_local_executable_overrides_global(run_mate, workspace, recorder):
    run_mate("config", "-g", "executables:tool=C:/does/not/exist/tool.exe")
    run_mate("config", f"executables:tool={sys.executable}")

    result = run_mate("tool", str(recorder))

    assert result.report == {name: 0 for name in workspace.folders}


@pytest.mark.xfail(strict=True, reason="arguments are stored as dict keys, so duplicated arguments collapse into one")
def test_duplicate_arguments_are_kept(run_mate, workspace, recorder):
    run_mate("rec", str(recorder), "same", "same")

    for folder in workspace.paths():
        assert recorded(folder)["argv"] == ["same", "same"]
