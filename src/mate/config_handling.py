import argparse
import importlib

from mate import config
from mate import output
from mate import globals


def initialize_configfiles(command_names: list[str]):    
    config_path = globals.get_global_configfile_path()
    global_config_created = config.create_configfile_if_none(config_path, config.DEFAULT_GLOBAL_CONFIG_CONTENT)
    
    config_path = globals.get_local_configfile_path()
    config.create_configfile_if_none(config_path, config.DEFAULT_LOCAL_CONFIG_CONTENT)    

    # Only populate global config file with default options from embedded commands if the global config was just created
    # TODO: Change the behaviour to check for existance of a section + entry. If not add it, else continue
    # This shall be the behaviour with which newly added and already existing modules will populate the config files
    if global_config_created:
        # For each command write config file default values if nothing yet present
        modules_config = {}
        for command in command_names:
            command_module = importlib.import_module(f".ops.{command}", package="mate")
            config_values = command_module.get_default_config()
            modules_config.update(config_values)
        config.write_configfile(modules_config, config.get_global_configfile_path(), "a")


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

        configs = config.read_configfiles(configfiles)
        output.info(f"Reading configuration files: {[str(p.resolve()) for p in configfiles]}")
        config.show_config_values(configs)
        globals.exit(globals.SUCCESS_CODE)

    if args.settings:
        if args.global_config:
            config_path = globals.get_global_configfile_path()
            output.info(f"Updating global config file in {config_path}")
        else:
            config_path = globals.get_local_configfile_path()
            output.info(f"Updating local config file in {config_path}")
        
        config.update_configfile(config_path, args.settings, args)
        
        return 0



