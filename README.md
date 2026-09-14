# Introduction and motivation for mate

Working on a C++ project (and maybe projects in other languages as well) with several repositories can be a challenge at best and an organisational nightmare at worst. mate was created to simplify, speed up or eliminate the repetitive manual work needed across many repositories.

mate is a small command-line tool that runs the **same operation across many project folders** in one go. Run it in a directory that contains several repositories, and it executes the command once per subfolder — so you don't have to do it by hand for each folder.

```
# Assume a workspace directory containing dir1, ..., dirN
# Running git status with mate is equivalent to doing this by hand:
some_root > mate git status 

# The command above does the following steps for you
some_root > cd dir1
some_root/dir1 > git status
some_root/dir1 > cd ..
some_root > cd dir2
some_root/dir2 > git status 
some_root/dir2 > cd .. 
# ....
some_root > cd dirN
some_root/dirN > git status

```

Typical use case: you keep a bunch of related git repositories checked out next to each other, and you regularly need to do the same thing in all of them — pull the latest changes, create new branches, run Conan commands, build projects, copy a file, commit changes, open pull requests, etc. With **mate** you only write the command once and it is executed for every folder.

# Core concepts
## Workspace and execution directories
mate is invoked in the directory that contains all of the desired repositories. This is called the workspace. It looks at the **direct subfolders** of the workspace and treats each one as an "execution directory" the command will be executed in. The list of execution directories contains all subfolders of the workspace, sorted alphabetically. When a command should not run in every folder, mate lets you select specific folders or ignore some altogether.

mate has the following CLI arguments to control the selection of execution folders:
- `-ef/--exclude`: Folders to exclude from the operation. This can also be done persistently with config files and the `folders:exclude` config entry.
- `-o/--only`: The only folders the command runs in.
- `-sf/--start-from`: Continue execution of a command that previously stopped due to an error.
- `--wsd`: Point mate at a workspace outside the current folder.

### Globbing directories
mate can also glob directories that fulfill a certain condition. For example, it can list the directories that have modifications.
Running `mate glob %git/has_changes[]%` outputs a list of directories with git modifications and also prints a ready-to-use `--only=dir1,dir2..` list.

## Config files
mate operates with two config files: `mate-global.toml`, in the user's home directory, and `mate-local.toml`, inside each workspace, located at `<wsd>/.mate/`. The values from the config files are loaded with each execution of mate. If the config files are not yet present, they will be created and populated with default values from embedded commands and required internal configuration entries.

Both the global and local configuration files can contain the same entries. Note that entries in the local config file take precedence over those in the global one: if an entry exists in both files, the local value wins. List entries are extended rather than overwritten, unless the CLI command explicitly requests overriding.


| Scope  | Location |
|--------|----------|
| Global | `<home>/.mate/mate-global.toml` |
| Local  | `<wsd>/.mate/mate-local.toml` |

The global config file contains by default the entry `folders:exclude=['.mate', '.git']`. These folders are always excluded from every execution. The local config file contains the same entry with a different default value, `folders:exclude=['build']`. The merged config therefore contains the exclusion list `['.mate', '.git', 'build']`.

You can inspect or edit them without opening a text editor. By default, mate modifies the local `mate-local.toml` file rather than the global one.

```bash
# print merged global, local or both config files
mate config --show [--global | --local]
# append a folder to the exclude list (local, by default)
mate config folders:exclude=node_modules 
# register an executable, globally
mate config executables:npp = C:/Program Files/Notepad++/notepad++.exe --global
# Create and populate a custom entry 
mate config some_section:some_entry="some_value" 
```

`--global/-g` / `--local/-l` pick which file to write to (local is the default); `--append/-a` (default), `--override/-o` and `--remove/-r` control how the value is merged.

## Placeholders
Arguments passed to a command can contain placeholders, enclosed in `%...%`, which are substituted per folder before execution. There are two types:

- **Config placeholders** — Have the format `%section:entry%`. The placeholder is replaced with the value of `entry` under `[section]` from the loaded config files, e.g. `%some_section:some_entry%` resolves to `"some_value"`.
- **Function placeholders** — Have the format `%function_name[]%`. They are evaluated for each execution directory. Their output is substituted into the command.
- Built-in functions include:
  - `folder_name[]` — returns the current folder's name.
  - `git_branch_name[]` — returns the currently checked-out git branch in that folder.

Example: `mate mkdir test_%folder_name[]%` creates `test_dir1`, `test_dir2` and so on in each execution directory.

**Note**: Printing a full list of functions is not yet possible; this is planned for later.
**Note**: These functions are not final and will be subject to changes and modifications.

## Commands 
A special feature of mate is its embedded (and soon local) commands. They are Python scripts that perform operations that no existing tool or shell command covers.

When you run `mate <command> ...`, mate decides *how* to run `<command>` by checking what kind of command it is:

1. **Embedded command** — a Python module (e.g. `gitea`, `copy`, `replace`) embedded in mate's source code. These modules implement richer, structured operations with their own arguments.
2. **Config-defined executable** — a path registered under the `[executables]` section of a config file (`mate config executables:<name>=<path>`). Call it by name, without the section prefix, e.g. `mate npp CMakeLists.txt`.
3. **Globally callable executable** — anything found on `PATH` (e.g. `git`, `npm`), run directly with the given arguments.
4. **Shell command** — anything else is handed off to the platform shell (e.g. PowerShell on Windows, `/bin/bash` on Linux) as a last resort. The shell can be changed in a config file.

This means `mate git status` runs `git status` in every project folder, `mate gitea create-pr ...` runs the embedded Gitea operation in every project folder, and `mate mkdir logs` falls through to the shell.


## Installation

Requirements: **Python 3.11+** (mate uses the standard-library `tomllib` for reading TOML).

```bash
git clone <this-repo>
cd automate
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt   # third-party dependencies: requests, colorama, tomli-w
pip install -e .                  # installs the `mate` command (editable install)
```

After installation, the `mate` command is available on your `PATH` (also runnable as `python -m mate`).

## Quick start

```bash
# Run from the parent folder that holds all your projects, or point --wsd at it
mate git status 

# Only execute in one specific directory
mate git pull --only dir1 --only dir3

# Exclude folders (comma-separated and/or repeatable)
mate git status -ef dir2,dir5 

# Resume a run starting at a given folder (e.g. after fixing an error halfway through)
mate git pull -sf dir3
```

## Embedded commands 
**Note**: These commands are subject to change and improvement.

### `gitea` — create or merge pull requests on a Gitea server
Requires `host` and `token` to be set under `[gitea]` in a config file:

```bash
mate config gitea:host=http://my-gitea-server:1234
mate config gitea:token=<personal-access-token>
```

```bash
mate gitea create-pr --target-branch dev --title "My change"
mate gitea merge-pr --merge-method squash --delete-branch
```

### `copy` — copy a file or folder into each execution directory
```bash
# Copy a.txt into each execution directory, named after that directory
mate copy --input d:/a.txt --destination %folder_name[]%.txt
```

### `replace` — edit a text file per folder
Replace a substring, or find/replace/append/prepend a matching line:
```bash
mate replace --file CMakeLists.txt --input "0.1.0" --output "0.2.0"
mate replace --file CMakeLists.txt --line "project(" --new-line "project(my_app)"
```

<!-- ## Extending Mate

- **New embedded command**: add a module under `src/mate/ops/` exposing `build_parser(parser)`, `main(cwd, args, env) -> int` and `get_default_config() -> dict`. Mate discovers it automatically by filename.
- **New placeholder function**: add a module under `src/mate/functions/` exposing `run(cwd: Path) -> str`. -->

## Project status / roadmap
mate is a personal hobby project of practical use to me (and hopefully others). I work on it whenever I have time. This project is developed with the help of AI but **NOT** by AI. It's mostly human-slop with parts of ai-slop.

mate is under active development. New features are coming, and existing ones may be changed and improved.
