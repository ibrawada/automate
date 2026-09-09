from __future__ import annotations
import sys
import tomllib
import tomli_w

from pathlib import Path


from mate import output




DEFAULT_LOCAL_CONFIG_CONTENT = {
    "folders": {
        "exclude":['build']
    }
}


DEFAULT_GLOBAL_CONFIG_CONTENT = {
    "folders": {
        "exclude":['.mate', '.git']
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



def load_config(path: str) -> dict:
    with open(path, "rb") as file:
        return tomllib.load(file)



def write_configfile(configfile_path: Path, config_content: dict, mode: str = "w") -> None:
    with open(configfile_path, "wb") as file:
        tomli_w.dump(config_content, file)



def create_configfile_if_none(configfile_path: Path, config_content: dict) -> bool:
    config_home_dir = configfile_path.parent
    config_home_dir.mkdir(parents=True, exist_ok=True)

    if not configfile_path.exists():
        write_configfile(configfile_path, config_content)

        return True
    # Nothing has been created
    return False



def create_section_option_if_none(config_content: dict, section: str, option: str, value: str) -> bool:
    # If no section -> create section
    if section not in config_content:
        config_content[section] = {}

    # If no option -> create option and exit
    if option not in config_content[section]:
        config_content[section][option] = value
        return True
    else:
        return False


def append_config_value(config_content: dict, section: str, option: str, value: str) -> dict:    

    was_created = create_section_option_if_none(config_content, section, option, value)
    if was_created:
        return config_content
    
    existing_value = config_content.get(section).get(option)

    # Only if the value is of type list -> Append the new value 
    if isinstance(existing_value, list):
        existing_value.append(value)
        config_content[section][option] = existing_value
    # Else override
    else:
        config_content[section][option] = value

    return config_content



def override_config_value(config_object: dict, section: str, option: str, value: str) -> dict:

    option_created = create_section_option_if_none(config_object, section, option, value)
    if option_created:
        return config_object
    
    # This is only required/valid for option of type list
    existing_value = config_object.get(section).get(option)

    if isinstance(existing_value, list):
        config_object[section][option] = value
    else:
        output.warning("Cannot override a value because the option: {section}{option} is not of type list")
    

    return config_object



def remove_config_entry(config_object: dict, section: str, option: str, value: str) -> dict:
    # Check whether the section and option exist
    # If only section provided -> remove the whole section
    config_has_section = section in config_object
    config_has_option = option in config_object.get(section, {})
    
    # Remove section 
    if section != "" and option == "" and value == "":
        if config_has_section:
            config_object.remove_section(section)
        else:    
            output.warning("Config has no section called {section}")
            return config_object
    # Remove the option from config
    elif section != "" and option != "" and value == "":
        if config_has_option:
            config_object.remove_option(section, option)
        else:
            output.warning("Config has no section / option called {section}:{option}")
            return config_object
    # Remove value. This is only applicabale for lists
    elif section != "" and option != "" and value != "":
        existing_value = config_object[section][option]
        if isinstance(existing_value, list):
            existing_value.remove(value)
            config_object.set(section, option, str(existing_value))
        else:
            output.warning("Nothing has been removed. The provided syntax is only allowed for list type options")
    else:
        output.warning("Wrong syntax used, nothing has been removed. Provide either section, and option and value")

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

    return (section, option, value)



def merge_configs(target_dict: dict, source_config: dict):
    """
    Merges settings from a ConfigParser object into a dictionary.
    It handles string representations of lists by parsing and merging them.
    """
    for section, options in source_config.items():
        if section not in target_dict:
            target_dict[section] = {}
        for option, value in options.items():
            if isinstance(value, list):
                if option in target_dict[section]:
                    target_dict[section][option].extend(value)
                else:
                    target_dict[section][option] = value
            else: # Not a list option -> set/override the value
                target_dict[section][option] = value



def show_config_values(configs: dict):    
    for section, map in configs.items():
        for k, v in map.items():
            output.message(f"{section}:{k} = {v}")


