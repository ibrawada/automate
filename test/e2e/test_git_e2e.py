import pytest

from .helpers import git, strip_ansi


pytestmark = pytest.mark.git


def test_git_init_in_every_project_folder(run_mate, git_workspace):
    result = run_mate("git", "init")

    assert result.report == {name: 0 for name in git_workspace.folders}
    for folder in git_workspace.paths():
        assert (folder / ".git").is_dir()
    assert not (git_workspace.path("build") / ".git").exists()
    assert not (git_workspace.root / ".mate" / ".git").exists()


def test_git_add_and_commit(run_mate, git_workspace):
    run_mate("git", "init")
    git_workspace.write("file.txt", "content")

    run_mate("git", "add", ".")
    result = run_mate("git", "commit", "-m", "initial commit")

    assert result.report == {name: 0 for name in git_workspace.folders}
    for folder in git_workspace.paths():
        assert git(folder, "log", "--format=%s") == "initial commit"
        assert git(folder, "status", "--porcelain") == ""


def test_commit_message_with_function_placeholder(run_mate, git_repos):
    git_repos.write("file.txt", "change")
    run_mate("git", "add", ".")

    run_mate("git", "commit", "-m", "feat: %folder_name[]%")

    for folder in git_repos.paths():
        assert git(folder, "log", "-1", "--format=%s") == f"feat: {folder.name}"


def test_checkout_branch_named_after_folder(run_mate, git_repos):
    result = run_mate("git", "checkout", "-b", "feature/%folder_name[]%")

    assert result.report == {name: 0 for name in git_repos.folders}
    for folder in git_repos.paths():
        assert git(folder, "branch", "--show-current") == f"feature/{folder.name}"


def test_git_branch_name_placeholder(run_mate, git_repos):
    run_mate("git", "checkout", "-b", "%folder_name[]%-dev")

    run_mate("git", "commit", "--allow-empty", "-m", "on %git_branch_name[]%")

    for folder in git_repos.paths():
        assert git(folder, "log", "-1", "--format=%s") == f"on {folder.name}-dev"


def test_config_placeholder_in_commit_message(run_mate, git_repos):
    run_mate("config", "vars:ticket=MATE-42")

    run_mate("git", "commit", "--allow-empty", "-m", "%vars:ticket%: empty commit")

    for folder in git_repos.paths():
        assert git(folder, "log", "-1", "--format=%s") == "MATE-42: empty commit"


@pytest.mark.parametrize("selection, expected", [
    (["--only=alpha,gamma"], ["alpha", "gamma"]),
    (["--only", "alpha", "--only", "beta"], ["alpha", "beta"]),
    (["--start-from", "beta"], ["beta", "gamma"]),
    (["--exclude=alpha,beta"], ["gamma"]),
    (["--only=alpha,beta,gamma", "--start-from", "beta", "--exclude", "gamma"], ["beta"]),
])
def test_folder_selection(run_mate, git_workspace, selection, expected):
    result = run_mate("git", "init", *selection)

    assert sorted(result.report) == expected
    for name in git_workspace.folders:
        assert (git_workspace.path(name) / ".git").is_dir() == (name in expected)


def test_failing_folder_is_reported_and_retry_suggested(run_mate, git_repos):
    # Only beta has something to commit, alpha and gamma will fail with "nothing to commit"
    (git_repos.path("beta") / "new.txt").write_text("new", encoding="utf-8")
    run_mate("git", "add", ".")

    result = run_mate("git", "commit", "-m", "only beta")

    assert result.report["beta"] == 0
    assert result.report["alpha"] != 0
    assert result.report["gamma"] != 0
    retry_line = next(line for line in strip_ansi(result.out).splitlines() if "To retry" in line)
    assert "alpha" in retry_line and "gamma" in retry_line and "beta" not in retry_line


def test_glob_folders_with_changes(run_mate, git_repos):
    (git_repos.path("alpha") / "dirty.txt").write_text("dirty", encoding="utf-8")

    result = run_mate("glob", "%git.has_changes[]%")

    assert "--only=alpha" in strip_ansi(result.out).splitlines()[-1]
