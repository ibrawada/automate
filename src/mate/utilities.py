import sys
import shutil
from pathlib import Path

from mate import output
from mate import globals

def get_shell_app_cmd(configs: dict) -> list[str]:    
    if sys.platform.startswith("win"):
        shell_app = configs["shell"]["windows"]
        return [shell_app, "-NoProfile", "-Command"]
    
    elif sys.platform.startswith("linux"):
        shell_app = configs["shell"]["linux"]
        return [shell_app, "-c"]
    
    else:
        output.error("No shell application defined in global/local config files")
        globals.exit(globals.ERROR_CODE)



def collect_embedded_commands(commands_dir: Path) -> list[str]:
    names = sorted(
        p.stem for p in commands_dir.glob("*.py") if p.stem != "__init__"
    )
    return names


def collect_folders(main_directory: Path, exclude_folders: list[str]) -> list[str]:
    # iterate over cwd and collect only the direct folder in level 1
    ret_folders = []
    for child_item in main_directory.iterdir():
        if any(ef in str(child_item) for ef in exclude_folders):
            continue
        if child_item.is_dir():
            ret_folders.append(str(child_item))
    return ret_folders



def is_globally_callable_command(command_name: str) -> bool:
    return shutil.which(command_name) != None
