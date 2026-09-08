from __future__ import annotations
import argparse
import ast
import sys
from pathlib import Path
from configparser import ConfigParser
from enum import Enum
from typing import Any

from mate import output




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


def configparser_to_dict(config_object: ConfigParser) -> dict:
    ret_dict = {}

    for section in config_object.sections():
        ret_dict[section] = dict(config_object.items(section))

    return ret_dict



def load_config(path: str) -> ConfigParser:
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
    

def split_config_entry(config_entry: str) -> tuple[str, str, str]:
    section = ""
    option = ""
    value = ""

    # Perform error checks
    if not ":" in config_entry or not "=" in config_entry:
        output.error(f"Wrong syntax for the provided setting: {config_entry}. Always use <section>:<entry>=<value> Syntax")
        sys.exit(1)

    section, option_value = config_entry.split(':', 1)
    option, value = option_value.split('=', 1)

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
        section, option, value  = split_config_entry(setting)
        
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



def show_config_values(configs: dict):    
    for section, map in configs.items():
        for k, v in map.items():
            output.message(f"{section}:{k} = {v}")


