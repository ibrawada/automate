import sys
import os
from pathlib import Path

# from mate import output

ERROR_CODE = 127
SUCCESS_CODE = 0


APP_NAME = "mate"
GLOBAL_CONFIG_FILE_NAME = "mate-global.toml"
LOCAL_CONFIG_FILE_NAME = "mate-local.toml"
WORKSPACE_DIR = Path(".")

EMBEDDED_COMMANDS_FOLDER = "commands"
# CONDITIONS_FOLDER = "conditions"
FUNCTIONS_FOLDER = "functions"


def set_workspace_dir(path: Path):
    global WORKSPACE_DIR
    WORKSPACE_DIR = path


def get_workspace_dir() -> Path:
    return WORKSPACE_DIR


def get_home_dir() -> Path:
    # Prefer Windows' %USERPROFILE% when available; fall back to Path.home()
    return Path(os.environ.get("USERPROFILE") or Path.home())


def get_local_config_dir() -> Path:
    return get_home_dir() / f".{APP_NAME}"


def get_global_configfile_path() -> Path:
    return get_local_config_dir() / GLOBAL_CONFIG_FILE_NAME


def get_local_configfile_path() -> Path:
    return WORKSPACE_DIR / Path(f".{APP_NAME}") / LOCAL_CONFIG_FILE_NAME



def exit_mate(exit_code: int = SUCCESS_CODE, str: function = ""):
    # Todo, maybe logging here for the function in which error occured
    sys.exit(exit_code)
