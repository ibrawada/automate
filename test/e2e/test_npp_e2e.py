"""Tests with the real Notepad++ registered as config executable.

Opt-in only (it opens a Notepad++ window): pytest -m npp
The Notepad++ location can be set with the environment variable MATE_NPP_PATH.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


pytestmark = [
    pytest.mark.npp,
    pytest.mark.skipif(not sys.platform.startswith("win"), reason="Notepad++ is only available on Windows"),
]

DEFAULT_NPP_PATH = Path(r"C:\Program Files\Notepad++\notepad++.exe")
NPP_WINDOW_CLASS = "Notepad++"


def find_npp_window() -> int:
    import ctypes
    return ctypes.windll.user32.FindWindowW(NPP_WINDOW_CLASS, None)


def window_title(hwnd: int) -> str:
    import ctypes
    buffer = ctypes.create_unicode_buffer(1024)
    ctypes.windll.user32.GetWindowTextW(hwnd, buffer, len(buffer))
    return buffer.value


def wait_for(condition, timeout: float = 15.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = condition()
        if value:
            return value
        time.sleep(0.2)
    return condition()


@pytest.fixture
def npp_path() -> Path:
    path = Path(os.environ.get("MATE_NPP_PATH", DEFAULT_NPP_PATH))
    if not path.exists():
        pytest.skip(f"Notepad++ not found at {path} (set MATE_NPP_PATH)")
    return path


@pytest.fixture
def npp_instance(npp_path):
    """Starts a dedicated Notepad++ instance. Further `notepad++.exe <file>` calls (as done by mate)
    hand the file over to this instance and return immediately instead of blocking."""
    if find_npp_window():
        pytest.skip("Notepad++ is already running; close it so the test does not open files in your session")

    process = subprocess.Popen([str(npp_path), "-nosession", "-notabbar"])
    hwnd = wait_for(find_npp_window)
    if not hwnd:
        process.kill()
        pytest.fail("Notepad++ window did not appear")

    yield hwnd

    process.kill()
    process.wait(timeout=10)


@pytest.fixture
def npp_workspace(run_mate_subprocess, workspace, npp_path):
    # Files must exist, otherwise Notepad++ asks with a dialog whether to create them
    workspace.write("readme.txt", "readme")
    for folder in workspace.paths():
        (folder / f"{folder.name}.txt").write_text(folder.name, encoding="utf-8")
    run_mate_subprocess("config", "-g", f"executables:npp={npp_path}")
    return workspace


def test_npp_opens_file_in_every_folder(run_mate_subprocess, npp_workspace, npp_instance, npp_path):
    result = run_mate_subprocess("npp", "readme.txt", timeout=60)

    assert result.code == 0
    assert result.report == {name: 0 for name in npp_workspace.folders}
    assert str(npp_path) in result.out
    # The last opened file is the active document
    last_file = npp_workspace.path(npp_workspace.folders[-1]) / "readme.txt"
    assert wait_for(lambda: str(last_file) in window_title(npp_instance)), window_title(npp_instance)


def test_npp_with_function_placeholder(run_mate_subprocess, npp_workspace, npp_instance):
    result = run_mate_subprocess("npp", "%folder_name[]%.txt", "--only=beta", timeout=60)

    assert result.report == {"beta": 0}
    expected_file = npp_workspace.path("beta") / "beta.txt"
    assert wait_for(lambda: str(expected_file) in window_title(npp_instance)), window_title(npp_instance)
