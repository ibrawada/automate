from dataclasses import dataclass
from enum import Enum, auto
import sys
import shutil
from pathlib import Path
from importlib import import_module
from types import ModuleType

from mate import output
from mate import globals



    
@dataclass(kw_only=True)
class MateModule:
    # name: str = "" # redundat because it is already the key for the dict
    path: str = "" # encoded as folder.[root].module_name
    module: ModuleType | None = None 



def get_shell_app_cmd(configs: dict) -> list[str]:    
    if sys.platform.startswith("win"):
        shell_app = configs["shell"]["windows"]
        return [shell_app, "-NoProfile", "-Command"]
    
    elif sys.platform.startswith("linux"):
        shell_app = configs["shell"]["linux"]
        return [shell_app, "-c"]
    
    else:
        output.error("No shell application defined in global/local config files")
        globals.exit_mate(globals.ERROR_CODE)



def collect_modules(modules_dir: Path) -> dict[str, MateModule]:
    # Todo: Modify this to be able to work recursively.
    # Also the collected name should contain root dir as well. eg. git/has_branch.py
    modules_names = sorted(
        p for p in modules_dir.rglob("*.py") if p.stem != "__init__"
    )

    
    ret_modules = {}
    for module in modules_names:
        print(str(module))
        module_path = ".".join(module.with_suffix("").parts)
        print(module_path)
        ret_modules[module.stem] = MateModule(path=module_path)
    
    return ret_modules



def load_modules(modules: dict[str, MateModule]):
    for _,module in modules.items():
        module.module = import_module(f"{module.path}", package="mate")



def collect_folders(main_directory: Path) -> list[str]:
    # iterate over cwd and collect only the direct folder in level 1
    ret_folders = []
    for child_item in main_directory.iterdir():
        if child_item.is_dir():
            ret_folders.append(str(child_item.name))
    return ret_folders



def remove_folders(working_dirs: list[str], exclude_folders: list[str]) -> list[str]:
    ret_dirs = []
    for dir in working_dirs:
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



def is_globally_callable_command(command_name: str) -> bool:
    return shutil.which(command_name) != None



def split_csv(value: str) -> list[str]:
    return [v.strip() for v in value.split(",") if v.strip()]