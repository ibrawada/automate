import copy
from pathlib import Path

from mate import config
from mate import config_handling
from mate import globals
from mate import main as mate_main
from mate import utilities

from .helpers import read_toml, strip_ansi


def expected_global_defaults() -> dict:
    """Global defaults plus the default config sections of every embedded command."""
    expected = copy.deepcopy(config_handling.DEFAULT_GLOBAL_CONFIG_CONTENT)
    commands = utilities.collect_modules(Path(globals.__file__).parent, globals.EMBEDDED_COMMANDS_FOLDER)
    utilities.load_modules(commands)
    for command in commands.values():
        config.merge_configs(target_dict=expected, source_config=command.module.get_default_config())
    return expected


# --- Creation ---------------------------------------------------------------

def test_first_run_creates_global_and_local_config(run_mate, workspace, global_config):
    assert not global_config.exists()
    assert not workspace.local_config.exists()

    result = run_mate("config", "--show")

    assert result.code == globals.SUCCESS_CODE
    assert read_toml(global_config) == expected_global_defaults()
    assert read_toml(workspace.local_config) == config_handling.DEFAULT_LOCAL_CONFIG_CONTENT


def test_first_run_adds_embedded_command_defaults(run_mate, global_config):
    run_mate("config", "--show")

    global_values = read_toml(global_config)
    assert global_values["gitea"] == {"host": "", "token": ""}
    assert "copy" in global_values


def test_existing_config_files_are_not_overwritten(mate_initialized, workspace, global_config):
    global_config.write_text('[vars]\nname = "custom"\n', encoding="utf-8")
    workspace.local_config.write_text('[folders]\nexclude = []\n', encoding="utf-8")

    mate_initialized("config", "--show")

    assert read_toml(global_config) == {"vars": {"name": "custom"}}
    assert read_toml(workspace.local_config) == {"folders": {"exclude": []}}


def test_each_workspace_gets_its_own_local_config(run_mate, workspace, tmp_path, global_config):
    run_mate("config", "vars:name=first")

    other = tmp_path / "other_ws"
    other.mkdir()
    mate_main.main(["--wsd", str(other), "config", "vars:name=second"])

    assert read_toml(workspace.local_config)["vars"]["name"] == "first"
    assert read_toml(other / ".mate" / globals.LOCAL_CONFIG_FILE_NAME)["vars"]["name"] == "second"


# --- Loading ----------------------------------------------------------------

def test_show_merges_global_and_local(mate_initialized):
    result = mate_initialized("config", "--show")

    lines = strip_ansi(result.out).splitlines()
    assert "folders:exclude = ['.mate', '.git', 'build']" in lines
    assert "shell:windows = powershell" in lines


def test_show_local_only(mate_initialized):
    result = mate_initialized("config", "--show", "-l")

    lines = strip_ansi(result.out).splitlines()
    assert "folders:exclude = ['build']" in lines
    assert not any(line.startswith("shell:") for line in lines)


def test_show_global_only(mate_initialized):
    result = mate_initialized("config", "--show", "-g")

    lines = strip_ansi(result.out).splitlines()
    assert "folders:exclude = ['.mate', '.git']" in lines
    assert any(line.startswith("shell:windows") for line in lines)


def test_local_value_overrides_global_value(mate_initialized, workspace):
    mate_initialized("config", "-g", "vars:greeting=global")
    mate_initialized("config", "vars:greeting=local")
    workspace.write("greeting.txt", "GREETING")

    result = mate_initialized("replace", "-f", "greeting.txt", "--input", "GREETING", "--output", "%vars:greeting%")

    assert result.report == {name: 0 for name in workspace.folders}
    for folder in workspace.paths():
        assert (folder / "greeting.txt").read_text(encoding="utf-8") == "local"


# --- Modification -----------------------------------------------------------

def test_set_value_writes_local_config_by_default(mate_initialized, workspace, global_config):
    global_before = read_toml(global_config)

    result = mate_initialized("config", "vars:name=foo")

    assert result.code == globals.SUCCESS_CODE
    assert read_toml(workspace.local_config)["vars"] == {"name": "foo"}
    assert read_toml(global_config) == global_before


def test_set_value_with_global_flag_writes_global_config(mate_initialized, workspace, global_config):
    mate_initialized("config", "-g", "vars:name=foo")

    assert read_toml(global_config)["vars"] == {"name": "foo"}
    assert "vars" not in read_toml(workspace.local_config)


def test_set_multiple_values_at_once(mate_initialized, workspace):
    mate_initialized("config", "vars:a=1", "vars:b=2", "other:c=3")

    local = read_toml(workspace.local_config)
    assert local["vars"] == {"a": "1", "b": "2"}
    assert local["other"] == {"c": "3"}


def test_set_value_containing_colon_and_equals(mate_initialized, workspace):
    mate_initialized("config", "-g", "executables:npp=C:/Program Files/Notepad++/notepad++.exe")
    mate_initialized("config", "vars:expr=a=b")

    assert read_toml(workspace.local_config)["vars"]["expr"] == "a=b"


def test_scalar_value_is_replaced(mate_initialized, workspace):
    mate_initialized("config", "vars:name=foo")
    mate_initialized("config", "vars:name=bar")

    assert read_toml(workspace.local_config)["vars"]["name"] == "bar"


def test_append_to_list_extends_it_and_is_applied(mate_initialized, workspace, tmp_path):
    (workspace.root / "dist").mkdir()
    source = tmp_path / "file.txt"
    source.write_text("content", encoding="utf-8")

    mate_initialized("config", "-a", "folders:exclude=dist")
    result = mate_initialized("copy", "-i", str(source))

    assert read_toml(workspace.local_config)["folders"]["exclude"] == ["build", "dist"]
    assert set(result.report) == set(workspace.folders)
    assert not (workspace.root / "dist" / "file.txt").exists()


def test_override_list_replaces_it(mate_initialized, workspace):
    mate_initialized("config", "-o", "folders:exclude=dist")

    assert read_toml(workspace.local_config)["folders"]["exclude"] == ["dist"]


def test_override_scalar_replaces_it(mate_initialized, workspace):
    mate_initialized("config", "vars:name=foo")

    result = mate_initialized("config", "-o", "vars:name=bar")

    assert result.code == globals.SUCCESS_CODE
    assert read_toml(workspace.local_config)["vars"]["name"] == "bar"


def test_invalid_setting_syntax_exits_with_error(mate_initialized, workspace):
    local_before = read_toml(workspace.local_config)

    result = mate_initialized("config", "novalue")

    assert result.code == globals.ERROR_CODE
    assert "[ERROR]" in strip_ansi(result.out)
    assert read_toml(workspace.local_config) == local_before


def test_remove_value_from_list(mate_initialized, workspace):
    mate_initialized("config", "-r", "folders:exclude=build")

    assert read_toml(workspace.local_config)["folders"]["exclude"] == []
