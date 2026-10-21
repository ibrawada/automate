import pytest

from mate import globals

from .helpers import strip_ansi


@pytest.fixture
def name_files(workspace):
    """Every project folder contains name.txt with the content NAME."""
    workspace.write("name.txt", "NAME")
    return workspace


def replace_name(run_mate, output_value: str):
    return run_mate("replace", "-f", "name.txt", "--input", "NAME", "--output", output_value)


def read_names(workspace) -> dict[str, str]:
    return {folder.name: (folder / "name.txt").read_text(encoding="utf-8") for folder in workspace.paths()}


# --- Config placeholders ----------------------------------------------------

def test_config_placeholder(run_mate, name_files):
    run_mate("config", "vars:name=configured")

    result = replace_name(run_mate, "%vars:name%")

    assert result.report == {name: 0 for name in name_files.folders}
    assert set(read_names(name_files).values()) == {"configured"}


def test_config_placeholder_from_global_config(run_mate, name_files):
    run_mate("config", "-g", "vars:name=from-global")

    replace_name(run_mate, "%vars:name%")

    assert set(read_names(name_files).values()) == {"from-global"}


def test_config_placeholder_with_path_value(run_mate, workspace, tmp_path):
    template = tmp_path / "template.txt"
    template.write_text("template", encoding="utf-8")
    run_mate("config", f"vars:template={template}")

    result = run_mate("copy", "-i", "%vars:template%")

    assert result.report == {name: 0 for name in workspace.folders}
    for folder in workspace.paths():
        assert (folder / "template.txt").read_text(encoding="utf-8") == "template"


def test_unknown_config_placeholder_exits_with_error(run_mate, name_files):
    result = replace_name(run_mate, "%vars:missing%")

    assert result.code == globals.ERROR_CODE
    assert "cannot be resolved from config" in strip_ansi(result.out)
    assert set(read_names(name_files).values()) == {"NAME"}


# --- Function placeholders --------------------------------------------------

def test_function_placeholder_is_resolved_per_folder(run_mate, name_files):
    replace_name(run_mate, "%folder_name[]%")

    assert read_names(name_files) == {name: name for name in name_files.folders}


def test_function_placeholder_with_prefix_and_suffix(run_mate, name_files):
    replace_name(run_mate, "pre_%folder_name[]%_post")

    assert read_names(name_files) == {name: f"pre_{name}_post" for name in name_files.folders}


def test_function_with_string_arguments(run_mate, name_files):
    replace_name(run_mate, "%to_upper[a,b]%")

    assert set(read_names(name_files).values()) == {"AB"}


def test_nested_function_placeholder(run_mate, name_files):
    replace_name(run_mate, "%to_upper[folder_name[]]%")

    assert read_names(name_files) == {name: name.upper() for name in name_files.folders}


def test_config_placeholder_as_function_argument(run_mate, name_files):
    run_mate("config", "vars:name=configured")

    replace_name(run_mate, "%to_upper[vars:name]%")

    assert set(read_names(name_files).values()) == {"CONFIGURED"}


def test_mixed_config_and_function_arguments(run_mate, name_files):
    run_mate("config", "vars:prefix=x-")

    replace_name(run_mate, "%to_upper[vars:prefix,folder_name[]]%")

    assert read_names(name_files) == {name: f"X-{name.upper()}" for name in name_files.folders}


def test_placeholders_in_multiple_arguments(run_mate, workspace, tmp_path):
    template = tmp_path / "template.txt"
    template.write_text("template", encoding="utf-8")
    run_mate("config", f"vars:template={template}")

    run_mate("copy", "-i", "%vars:template%", "-d", "%folder_name[]%.txt")

    for folder in workspace.paths():
        assert (folder / f"{folder.name}.txt").read_text(encoding="utf-8") == "template"


@pytest.mark.xfail(strict=True, raises=KeyError, reason="unknown function names raise a KeyError instead of a clean error")
def test_unknown_function_placeholder_exits_with_error(run_mate, name_files):
    result = replace_name(run_mate, "%no_such_function[]%")

    assert result.code == globals.ERROR_CODE


@pytest.mark.xfail(strict=True, reason="-o of an embedded command is consumed by mate's own -o/--only option")
def test_short_option_of_embedded_command_is_passed_through(run_mate, name_files):
    run_mate("replace", "-f", "name.txt", "-i", "NAME", "-o", "%folder_name[]%")

    assert read_names(name_files) == {name: name for name in name_files.folders}
