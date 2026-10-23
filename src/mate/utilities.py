from dataclasses import dataclass
from enum import Enum, auto
import sys
import shlex
import shutil
from pathlib import Path
from importlib import import_module
from types import ModuleType

from mate import output
from mate import globals

    
@dataclass(kw_only=True)
class MateModule:
    name: str = ""
    path: str = "" # encoded as folder.[root].module_name
    module: ModuleType | None = None 



POWERSHELL_APPS = ("powershell", "pwsh")
CMD_APPS = ("cmd",)


def get_shell_platform_keys() -> list[str]:
    # Config keys to look up under [shell], in priority order
    if sys.platform.startswith("win"):
        return ["windows"]
    if sys.platform == "darwin":
        return ["macos", "linux"]
    return ["linux"]


def get_shell_kind(shell_app: str) -> str:
    name = Path(shell_app).stem.lower()
    if name in POWERSHELL_APPS:
        return "powershell"
    if name in CMD_APPS:
        return "cmd"
    return "posix"


def get_shell_app_cmd(configs: dict) -> list[str]:
    shell_configs = configs.get("shell", {})
    platform_keys = get_shell_platform_keys()

    shell_app = next((shell_configs[key] for key in platform_keys if shell_configs.get(key)), None)
    if not shell_app:
        output.error(f"No shell application defined in global/local config files. Set it with: mate config shell:{platform_keys[0]}=<shell> -g")
        globals.exit_mate(globals.ERROR_CODE)

    if shutil.which(shell_app) is None:
        output.error(f"Shell application not found: {shell_app}")
        globals.exit_mate(globals.ERROR_CODE)

    kind = get_shell_kind(shell_app)
    if kind == "powershell":
        return [shell_app, "-NoProfile", "-Command"]
    if kind == "cmd":
        return [shell_app, "/c"]
    return [shell_app, "-c"]


def quote_shell_arg(arg: str, shell_kind: str) -> str:
    # Only quote args that would otherwise be split or lost, so shell syntax (|, >, $VAR) still works
    if arg and not any(c.isspace() or c in "'\"" for c in arg):
        return arg

    if shell_kind == "powershell":
        return "'" + arg.replace("'", "''") + "'"
    if shell_kind == "cmd":
        return '"' + arg.replace('"', '""') + '"'
    return shlex.quote(arg)


def build_shell_command_line(shell_app: str, command: str, args: list[str]) -> str:
    kind = get_shell_kind(shell_app)
    return " ".join([command, *(quote_shell_arg(arg, kind) for arg in args)])



def collect_modules(modules_root_dir: Path, modules_home_dir: Path | None = None) -> dict[str, MateModule]:

    modules_path = modules_root_dir / modules_home_dir
    modules_names = sorted(
        p for p in modules_path.rglob("*.py") if p.stem != "__init__"
    )
    
    ret_modules = {}
    for module in modules_names:
        module_path = ".".join(module.relative_to(modules_root_dir).with_suffix("").parts)
        module_name = ".".join(module.relative_to(modules_root_dir / modules_home_dir).with_suffix("").parts)
        ret_modules[module_name] = MateModule(name=module_name, path=module_path)
    
    return ret_modules



def load_modules(modules: dict[str, MateModule]):
    for _,module in modules.items():
        module.module = import_module(f".{module.path}", package="mate")



def collect_folders(main_directory: Path) -> list[str]:
    # iterate over the workspace directory and collect only the direct folder in level 1
    ret_folders = []
    for child_item in main_directory.iterdir():
        if child_item.is_dir():
            ret_folders.append(str(child_item.name))

    ret_folders.sort(key=str.casefold)
    return ret_folders



def remove_folders(execution_dirs: list[str], exclude_folders: list[str]) -> list[str]:
    ret_dirs = []
    for dir in execution_dirs:
        if dir not in exclude_folders:
            ret_dirs.append(dir)
    return ret_dirs



def remove_folders_until(folders: list[str], start_folder: str) -> list[str]:
    index_start_folder = folders.index(str(Path(start_folder)))
    ret_folders = folders[index_start_folder:]
    return ret_folders



def split_csv_args(args: list[list[str]]) -> list[str]:
    return [str(Path(dir.strip()))
            for group in args
            for dir in group.split(",")
            if dir.strip()]



def split_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]



def is_callable_executable(command_name: str) -> bool:
    return shutil.which(command_name) != None


