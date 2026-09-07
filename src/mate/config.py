from __future__ import annotations
import argparse
import os
import ast
import sys
import importlib
from pathlib import Path
from configparser import ConfigParser
from enum import Enum
from typing import Any
from mate import output


APP_NAME = "mate"
GLOBAL_CONFIG_FILE_NAME = "mate-global.conf"
LOCAL_CONFIG_FILE_NAME = "mate-local.conf"
CWD = Path(".")

# ---- paths ---------------------------------------------------------------
def set_cwd(path: Path):
    global CWD
    CWD = path

def get_cwd() -> Path:
    return CWD

def get_home_dir() -> Path:
    # Prefer Windows' %USERPROFILE% when available; fall back to Path.home()
    return Path(os.environ.get("USERPROFILE") or Path.home())

def get_local_config_dir() -> Path:
    return get_home_dir() / f".{APP_NAME}"

def get_global_configfile_path() -> Path:
    return get_local_config_dir() / GLOBAL_CONFIG_FILE_NAME

def get_local_configfile_path() -> Path:
    return CWD / Path(f".{APP_NAME}") / LOCAL_CONFIG_FILE_NAME


# ---- config I/O ----------------------------------------------------------

DEFAULT_LOCAL_CONFIG_CONTENT = {
    "folders": {
        "exclude":"['build']"
    }
}


DEFAULT_GLOBAL_CONFIG_CONTENT = {
    "folders": {
        "exclude":"['.mate', '.git']"
    },
    "executables":
    {

    },
    "shell":
    {
        "windows" : "powershell",
        "linux": "/bin/bash"
    }
}






def create_configfile_if_none(configfile_path, config_content) -> bool:
    config_home_dir = configfile_path.parent
    config_home_dir.mkdir(parents=True, exist_ok=True)

    if not configfile_path.exists():
        config_object = ConfigParser()
        for section, values in config_content.items():
            config_object[section] = values
        write_configfile(config_object, configfile_path)

        return True
    # Nothing has been created
    return False



def write_configfile(config_content: ConfigParser | dict, configfile_path: Path, mode: str = "w") -> None:
    with configfile_path.open(mode, encoding="utf-8") as f:
        if isinstance(config_content, dict):
            configparser = ConfigParser()
            configparser.read_dict(config_content)
            configparser.write(f)
        else:
            config_content.write(f)



def load_config(path) -> ConfigParser:
    cfg = ConfigParser()    
    cfg.read(path, encoding="utf-8")
    return cfg



def append_config_value(config_object: ConfigParser, section: str, option: str, value: str) -> ConfigParser:    
    # Case 1: If no section and option with the name -> create everything 
    if not config_object.has_option(section, option):
        if not config_object.has_section(section):
            config_object.add_section(section)

        config_object.set(section, option, value)
        return config_object

    # Read in existing value and check its type -> depending on whether list or not the append will differ
    existing_value = config_object.get(section, option)
    try:
        existing_value_typed = ast.literal_eval(existing_value)
    except (ValueError, SyntaxError):
        existing_value_typed = existing_value        

    if isinstance(existing_value_typed, list):
        existing_value_typed.append(value)
        config_object.set(section, option, str(existing_value_typed))
    else: # Normal value -> override
        config_object.set(section, option, value)

    return config_object



def override_config_value(config_object: ConfigParser, section: str, option: str, value: str) -> ConfigParser:
    # This is only required/valid for option of type list
    existing_value = config_object.get(section, option)
    try:
        existing_value_typed = ast.literal_eval(existing_value)
    except (ValueError, SyntaxError):
        existing_value_typed = existing_value

    if isinstance(existing_value_typed, list):
        config_object.set(section, option, value)
    else:
        print("[WARNING] Cannot override a value because the option is not of type list")
    

    return config_object



def remove_config_value(config_object: ConfigParser, section: str, option: str, value: str) -> ConfigParser:
    # Check whether the section and option exist
    # If only section provided -> remove the whole section
    config_has_section = config_object.has_section(section)
    config_has_option = config_object.has_option(section, option)
    
    # Remove section 
    if section != "" and option == "" and value == "":
        if not config_has_section:
            print("[WARNING] Config has no section called {section}")
            return config_object        
        config_object.remove_section(section)
    # Remove the option from config
    elif section != "" and option != "" and value == "":
        if not config_has_option:
            print("[WARNING] Config has no section / option called {section}:{option}")
            return config_object
        config_object.remove_option(section, option)
    # Remove value. This is only applicabale for lists
    elif section != "" and option != "" and value != "":
        # Check if the option exist and that its a list
        existing_value = config_object.get(section, option)
        try:
            # Safely evaluate string to a Python literal (e.g., "['a', 'b']" -> ['a', 'b'])
            # value = ast.literal_eval(existing_value)
            existing_value_typed = ast.literal_eval(existing_value)
        except (ValueError, SyntaxError):
            existing_value_typed = existing_value

        if isinstance(existing_value_typed, list):
            existing_value_typed.remove(value)
            config_object.set(section, option, str(existing_value_typed))
        else:
            print("[WARNING] Nothing has been removed. The provided syntax is only allowed for list type options")
        # except (ValueError, SyntaxError):
        #     # Not a literal, treat as a plain string
        #     # value = value_str
        #     print("[WARNING] Nothing has been removed. The provided syntax is only allowed for list type options")
    else:
        print("[WARNING] Wrong syntax used, nothing has been removed")

    return config_object
    

def split_config_entry(setting: str) -> tuple[str, str, str]:
    # Perform error checks
    section = ""
    option = ""
    value = ""

    if not ":" in setting or not "=" in setting:
        output.error(f"Wrong syntax for the provided setting: {setting}. Always use <section>:<entry>=<value> Syntax")
        sys.exit(1)
    # if ":" in setting:
    section, option_value = setting.split(':', 1)
        
        # if "=" in option_value:
    option, value = option_value.split('=', 1)
        # else:
        #     # Only option provided
        #     option = option_value

    # only section provided nothing else
    # TODO: Check when this case happens
    # else:
    #     section = setting

    return (section, option, value)



def update_configfile(config_path: Path, settings: list[str], args: argparse.Namespace):
    """Updates a configuration file with new settings."""
    config_object = ConfigParser()
    config_object.read(config_path)

    for setting in settings:
        section, option, value, status = split_config_entry(setting)

        if status == False:
            return
        
        if args.append:
            append_config_value(config_object, section, option, value)
        elif args.remove:
            remove_config_value(config_object, section, option, value)
        elif args.override:
            override_config_value(config_object, section, option, value)
        else:
            append_config_value(config_object, section, option, value)

    write_configfile(config_object, config_path)



def merge_configs(target_dict: dict, source_config: ConfigParser):
    """
    Merges settings from a ConfigParser object into a dictionary.
    It handles string representations of lists by parsing and merging them.
    """
    for section in source_config.sections():
        if section not in target_dict:
            target_dict[section] = {}
        for key, value_str in source_config.items(section):
            try:
                # Safely evaluate string to a Python literal (e.g., "['a', 'b']" -> ['a', 'b'])
                value = ast.literal_eval(value_str)
            except (ValueError, SyntaxError):
                # Not a literal, treat as a plain string
                value = value_str

            if isinstance(value, list):# and key in target_dict[section] and isinstance(target_dict[section][key], list):
                if key in target_dict[section]:
                    target_dict[section][key].extend(value)
                else:
                    target_dict[section][key] = value
            else: # Not a list option -> set/override the value
                target_dict[section][key] = value


def read_configfiles(configfiles: list[str]) -> dict[str, dict[str, Any]]:
    combined_configs = {}
    
    for configfile in configfiles:
        config_values = load_config(configfile)
        merge_configs(target_dict=combined_configs, source_config=config_values)
    
    return combined_configs



def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=APP_NAME,
        description=f"{APP_NAME}: example tool that uses a per-user config file",
    )
    p.add_argument(
        "--global", "-g",
        dest="global_config",
        action="store_true",
        help="Target the global configuration."
    )
    p.add_argument(
        "--local", "-l",
        dest="local_config",
        action="store_true",
        help="Target the local configuration (The default behaviour)."
    )
    p.add_argument(
        "--append", "-a",
        action="store_true",
        help="Append a value to a list in the config (not yet implemented)."
    )
    p.add_argument(
        "--remove", "-r",
        action="store_true",
        help="Remove a value from a list in the config (not yet implemented)."
    )
    p.add_argument(
        "--override", "-o",
        action="store_true",
        help="Override a list based value in the config (not yet implemented)."
    )
    p.add_argument(
        "--show", 
        action="store_true",
        help="Remove a value from a list in the config (not yet implemented)."
    )
    p.add_argument(
        "settings",
        nargs="*",
        help="Settings to update, in 'section:key=value' format."
    )

    return p

# Todo:
# Add ability to show only local or global config values 
# eg. "mate config --show --globa|--local"
# -> This would mean that read_configfiles will have to accept parameters to which config shall be read in
def handle_config_arguments(argv: list[str] | None = None):
    args = build_parser().parse_args(argv)


    if args.show:
        configfiles = [get_global_configfile_path(), get_local_configfile_path()]
        if args.local_config:
            configfiles = [get_local_configfile_path()]
        if args.global_config:
            configfiles = [get_global_configfile_path()]

        configs = read_configfiles(configfiles)

        output.info(f"Reading configuration files: {[str(p.resolve()) for p in configfiles]}")
        for section, map in configs.items():
            for k, v in map.items():
                output.message(f"{section}:{k} = {v}")
        return 0

    if args.settings:
        if args.global_config:
            config_path = get_global_configfile_path()
            output.info(f"Updating global config file in {config_path}")
        else:
            config_path = get_local_configfile_path()
            output.info(f"Updating local config file in {config_path}")
        
        update_configfile(config_path, args.settings, args)
        
        return 0



