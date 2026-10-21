import pytest

from .helpers import strip_ansi


def executed_folders(result) -> list[str]:
    """Folder names from the "[INFO] Execution on following folders:" line, in execution order."""
    lines = strip_ansi(result.out).splitlines()
    index = next(i for i, line in enumerate(lines) if "Execution on following folders" in line)
    return [name.strip() for name in lines[index + 1].split(",") if name.strip()]


@pytest.fixture
def mixed_case_workspace(workspace):
    for name in ["Delta", "epsilon", ".hidden_by_config"]:
        (workspace.root / name).mkdir()
    (workspace.root / "not_a_folder.txt").write_text("file")
    return workspace


def test_folders_are_sorted_case_insensitive(run_mate, mixed_case_workspace):
    run_mate("config", "-a", "folders:exclude=.hidden_by_config")

    result = run_mate("exit", "0")

    assert executed_folders(result) == ["alpha", "beta", "Delta", "epsilon", "gamma"]


def test_default_excludes_are_applied(run_mate, workspace):
    (workspace.root / ".git").mkdir()

    result = run_mate("exit", "0")

    assert executed_folders(result) == workspace.folders


@pytest.mark.parametrize("selection, expected", [
    (["--only=gamma,alpha"], ["gamma", "alpha"]),
    (["-o", "beta"], ["beta"]),
    (["-sf", "beta"], ["beta", "gamma"]),
    (["-ef", "beta"], ["alpha", "gamma"]),
    (["--exclude=alpha", "--exclude=gamma"], ["beta"]),
    (["--only=alpha,beta,gamma", "--start-from=beta", "--exclude=gamma"], ["beta"]),
])
def test_folder_selection_options(run_mate, workspace, selection, expected):
    result = run_mate("exit", "0", *selection)

    assert executed_folders(result) == expected
    assert sorted(result.report) == sorted(expected)


def test_only_can_select_an_excluded_folder(run_mate, workspace):
    result = run_mate("exit", "0", "--only=build")

    assert executed_folders(result) == ["build"]


@pytest.mark.xfail(strict=True, raises=ValueError, reason="a missing --start-from folder raises an uncaught ValueError")
def test_unknown_start_from_folder_exits_with_error(run_mate, workspace):
    result = run_mate("exit", "0", "--start-from", "does_not_exist")

    assert result.code == 127
