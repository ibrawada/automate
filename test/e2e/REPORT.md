# End-to-end tests for mate: summary

I've written the end-to-end tests for mate and fixed the crash that blocked every first run.

The default run gives:
- 73 passed
- 1 skipped (the POSIX-only shell test)
- 6 expected failures
- 2 Notepad++ tests that are left out unless you ask for them

Those 2 also pass on your machine with `pytest -m npp`. Your real `~/.mate` config files were not touched.

## How it works
- Each test builds a fresh workspace with the folders `alpha`, `beta`, `gamma` and `build`. `build` is excluded by the default local config.
- `USERPROFILE`/`HOME` point at a temp folder, so the global config is isolated too.
- Git runs with its own temporary config, so your git settings don't affect the results.
- Tests check real results: config files on disk, git log and branches, created folders, and the per-folder `[REPORT]` line.

## What's covered
All tests are in `test/e2e/`.

- **Config** (`test_config_e2e.py`): files created on first run, never overwritten later, and kept separate per workspace. Also `--show` with `-g`/`-l`, setting values locally and globally, appending to lists, local values winning over global ones, and invalid syntax.
- **Git** (`test_git_e2e.py`): `init`, `add` and `commit`, plus a commit message or branch name built from `%folder_name[]%`, `%git_branch_name[]%` or `%vars:x%`. It also covers `--only`/`--start-from`/`--exclude`, a failing folder showing up with the retry hint, and `glob %git.has_changes[]%`.
- **Shell** (`test_shell_e2e.py`): `mkdir` with plain names, names with spaces, and placeholders. It also checks that non-zero exit codes are reported, that the default shell is PowerShell, that switching to `cmd` (or `sh` on Linux/macOS) works, and that an unknown shell gives a clean error.
- **Notepad++** (`test_npp_e2e.py`):
  - The tests start their own Notepad++ instance and check its window title to confirm the right file opened.
  - Notepad++ only runs with `pytest -m npp`, because it opens a window.
  - The tests skip if Notepad++ is already open, so they never put files into your own session.
- **Other executables** (`test_executables_e2e.py`): a small Python script registered under `executables` records what it was called with in each folder. A missing executable is reported as 127.
- **Placeholders** (`test_placeholders_e2e.py`): config values (local and global), functions, text around a placeholder, nested and multi-argument functions, and mixing config values with functions. An unknown config key exits with 127.
- **Folders** (`test_folders_e2e.py`) and **real process** (`test_smoke_subprocess.py`): folder ordering and exclusion, and a few runs through `python -m mate`.

## Changes outside the tests
- `src/mate/config_handling.py:28`: the first run in a fresh home folder crashed. It now merges each command's default settings into the global config. I reverted this fix temporarily and the two first-run tests failed, so they do catch the bug.
- `src/mate/globals.py:48` and `src/mate/placeholderslib.py`: fixed type hints that crash on Python 3.11–3.13.
- `pyproject.toml`: pytest settings, a `test` extra, and the missing `gitpython` dependency.
- `test/conftest.py`: stops pytest from collecting the old scratch test files.

## Known bugs, marked as expected failures
Each will start failing loudly once someone fixes it, so the marker can be removed:
- `config -r` crashes.
- `config -o` on a list stores a single string instead of a list.
- An unknown function name in a placeholder crashes instead of giving a clean error.
- `-o` after an embedded command is taken as mate's own `--only`. For example, `replace ... -o X` doesn't work; you have to write `--output`.
- Repeated identical arguments are collapsed into one, so `same same` is passed as just `same`.
- A `--start-from` folder that doesn't exist crashes.

Nothing is committed yet. I didn't do the optional README update (a "Running tests" section and correcting `git/has_changes[]` to `git.has_changes[]`).
