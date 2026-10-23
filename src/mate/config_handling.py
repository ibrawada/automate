import argparse
import importlib
from pathlib import Path
from typing import Any

from mate import config
from mate import output
from mate import globals
from mate.utilities import MateModule



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
        "linux": "/bin/bash",
        "macos": "/bin/zsh"
    }
}



def initialize_configfiles(commands: dict[str, MateModule]):    
    config_path = globals.get_global_configfile_path()
    global_config_created = config.create_configfile_if_none(config_path, DEFAULT_GLOBAL_CONFIG_CONTENT)
    
    config_path = globals.get_local_configfile_path()
    config.create_configfile_if_none(config_path, DEFAULT_LOCAL_CONFIG_CONTENT)    

    # Only populate global config file with default options from embedded commands if the global config was just created
    # TODO: Change the behaviour to check for existance of a section + entry. If not add it, else continue
    # This shall be the behaviour with which newly added and already existing modules will populate the config files
    if global_config_created:
        # For each command write config file default values if nothing yet present
        modules_config = {}
        for _, command in commands.items():
            # command_module = importlib.import_module(f".ops.{command}", package="mate")
            config_values = command.module.get_default_config()
            modules_config.update(config_values)

        global_config_path = globals.get_global_configfile_path()
        global_config = config.load_config(global_config_path)
        config.merge_configs(target_dict=global_config, source_config=modules_config)
        config.write_configfile(global_config_path, global_config)



def read_configfiles(configfiles: list[str]) -> dict[str, Any]:
    combined_configs = {}
    
    for configfile in configfiles:
        config_values = config.load_config(configfile)
        config.merge_configs(target_dict=combined_configs, source_config=config_values)
    
    return combined_configs



def update_configfile(config_path: Path, settings: list[str], args: argparse.Namespace):
    """Updates a configuration file with new settings."""
    config_content = config.load_config(config_path)

    for setting in settings:
        if not config.is_config_entry_syntax_correct(setting):
            globals.exit_mate(exit_code=globals.ERROR_CODE, message=f"Wrong syntax for the provided setting: {setting}. Always use <section>:<entry>=<value> Syntax")

        section, option, value  = config.split_config_entry(setting)

        has_section, has_option = config.entry_exists(config_content, section, option)

        if args.remove:
            if not has_section:
                output.warning(f"Provided section:{section} was not found in the config. Use mate config --show to list all available config entries")
                globals.exit_mate(globals.ERROR_CODE)
            elif option != "" and not has_option:
                output.warning(f"Provided option:{option} was not found in the config. Use mate config --show to list all available config entries")
                globals.exit_mate(globals.ERROR_CODE)
            else:
                config.remove_value(config_content, section, option, value)
        
        elif args.override:
            if not has_option:
                config.create_section_and_option_if_none(config_content, section, option, value)            
            else:
                config.override_value(config_content, section, option, value)
        
        else: # This case handle args.append and no args provided (default = append)
            if not has_option:
                config.create_section_and_option_if_none(config_content, section, option, value)
            else:
                config.append_value(config_content, section, option, value)

    config.write_configfile(config_path, config_content)



def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=globals.APP_NAME,
        description=f"{globals.APP_NAME}: example tool that uses a per-user config file",
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
        configfiles = [globals.get_global_configfile_path(), globals.get_local_configfile_path()]
        if args.local_config:
            configfiles = [globals.get_local_configfile_path()]
        if args.global_config:
            configfiles = [globals.get_global_configfile_path()]

        configs = read_configfiles(configfiles)
        output.info(f"Reading configuration files: {[str(p.resolve()) for p in configfiles]}")
        config.show_config_values(configs)
        

    if args.settings:
        if args.global_config:
            config_path = globals.get_global_configfile_path()
            output.info(f"Updating global config file in {config_path}")
        else:
            config_path = globals.get_local_configfile_path()
            output.info(f"Updating local config file in {config_path}")
        
        update_configfile(config_path, args.settings, args)
        
    globals.exit_mate(globals.SUCCESS_CODE)



