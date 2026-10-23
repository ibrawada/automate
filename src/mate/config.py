from __future__ import annotations
import sys
import tomllib
import tomli_w

from pathlib import Path


from mate import output



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



def entry_exists(config_content: dict, section: str, option: str) -> tuple[bool, bool]:
    """
    Checks whether a section and an option within it exist in the config.
    Returns a tuple (has_section, has_option):
    - has_section: True if the section exists in the config
    - has_option: True if the option exists within that section
    (always False if the section does not exist)
    """
    # No section -> Also no option 
    if section not in config_content:
        return (False, False)

    # Section exists but not the option
    if option not in config_content[section]:
        return (True, False)

    # When both exist
    return (True, True)



def create_section_and_option_if_none(config_content: dict, section: str, option: str, value: str) -> bool:
    has_section, has_option = entry_exists(config_content, section, option)

    # If no section -> create section
    if not has_section:
        config_content[section] = {}

    # If no option -> create option and exit
    if not has_option:
        config_content[section][option] = value
        return True
    else:
        return False


# pre-condition:
# - Section and option with value(s) must exist
def append_value(config_content: dict, section: str, option: str, value: str) -> dict:
    # was_created = create_section_and_option_if_none(config_content, section, option, value)
    # if was_created:
    #     return config_content
    
    existing_value = config_content.get(section).get(option)

    # Only if the value is of type list -> Append the new value 
    if isinstance(existing_value, list):
        existing_value.append(value)
        config_content[section][option] = existing_value
    # Else override
    else:
        config_content[section][option] = value

    return config_content



def override_value(config_object: dict, section: str, option: str, value: str | list[str]) -> dict:
    # This is only required/valid for option of type list
    existing_value = config_object.get(section).get(option)

    if isinstance(existing_value, list):
        if isinstance(value, list):
            config_object[section][option] = value
        else: # Create a list from given value string
            config_object[section][option] = [value]
    else:
        config_object[section][option] = value
    

    return config_object



def remove_value(config_object: dict, section: str, option: str, value: str) -> dict:
    # Remove section 
    if section != "" and option == "" and value == "":        
        # config_object.remove_section(section)
        config_object.pop(section)
        
    # Remove the option from config
    elif section != "" and option != "" and value == "":        
        # config_object.remove_option(section, option)
        config_object[section].pop(option)
        
    # Remove value. This is only applicabale for lists
    elif section != "" and option != "" and value != "":
        existing_value = config_object[section][option]
        if isinstance(existing_value, list):
            if isinstance(value, list):
                for val in value:
                    existing_value.remove(val)
            else:
                existing_value.remove(value)

            config_object[section][option] = existing_value
        else:
            output.warning("Nothing has been removed. The provided syntax is only allowed for list type options")
    else:
        output.warning("Wrong syntax used, nothing has been removed. Provide either section, and option and value")

    return config_object



def is_config_entry_syntax_correct(config_entry: str) -> bool:
    if not ":" in config_entry or not "=" in config_entry:        
        return False
    return True


# Pre-condition
# - Syntax of the entry is correct
def split_config_entry(config_entry: str) -> tuple[str, str, str]:
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


