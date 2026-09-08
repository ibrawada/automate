#!/usr/bin/env python3
import argparse
import shutil
import subprocess
import sys
from pathlib import Path
import importlib
from types import ModuleType


from mate import placeholderslib
from mate import config
from mate import output
from mate import globals
from mate import executors
from mate import utilities
from mate import config_handling



def create_command_parser(commands):
    p = argparse.ArgumentParser(
        prog=f"python {Path(sys.argv[0]).name}",
        description="command runner",
        add_help=False,
    )
    
    p.add_argument("command", nargs="?", help=f"One of: {', '.join(sorted(commands))}")
    p.add_argument("-h", "--help", action="store_true", help="Show this help")

    return p



def main(cli_arguments=None):
    """Main command-line-interface entry point."""
    if cli_arguments is None:
        cli_arguments = sys.argv[1:]

    # --- Initial Setup: Parse only --cwd to set the context ---
    # This is required in order to define/locate the current working directory and create/read according local-mate.conf file
    cwd_parser = argparse.ArgumentParser(add_help=False)
    cwd_parser.add_argument("--cwd", type=Path, default=".")
    
    cwd_config_arg, command_arguments = cwd_parser.parse_known_args(cli_arguments)
    current_working_dir = cwd_config_arg.cwd
    globals.set_cwd(current_working_dir)

    embedded_commands_names = utilities.collect_embedded_commands(Path(__file__).parent / "ops")
    
    # Initialize config files is required
    config_handling.initialize_configfiles(embedded_commands_names)

    # Check if command_arguments contains "config" instead of actual command (eg. [config, var:test=test])
    # - has length more than 2 elements -> user provided a value to be modified
    # - and if the 0th element is actually config -> only then update configs
    if len(command_arguments) >= 2 and command_arguments[0] == "config":
        # Provide only the config content to be update (strip the "config" from the list)
        return config_handling.handle_config_arguments(command_arguments[1:])
        

    # REQ-###: System shall load global config file first followed by local config file
    # REQ-###: System shall override global config value by local config value if present in both files
    # Current behaviour will load the 
    configs_values = config.read_configfiles([globals.get_global_configfile_path(), globals.get_local_configfile_path()])

    command_parser = create_command_parser(embedded_commands_names)
    command_arg, rest_arguments = command_parser.parse_known_args(command_arguments)
    
    if command_arg.help and not command_arg.command:
        command_parser.print_help()
        return globals.SUCCESS_CODE
    
    if not command_arg.command:
        command_parser.error("a command is required.")
        return globals.ERROR_CODE

    working_directories = utilities.collect_folders(current_working_dir, configs_values["folders"]["exclude"])


    extracted_placeholders = placeholderslib.extract_argument_placeholders(rest_arguments)
    substitued_arguments = placeholderslib.substitute_argument_placeholders_from_configs(rest_arguments, extracted_placeholders, configs_values)

    ## Case 1:
    # Execute an embedded command (aka python script)
    command_name = command_arg.command 
    if command_name in embedded_commands_names:
        return executors.execute_embedded_command(command_name, substitued_arguments, configs_values.get(command_name, {}), working_directories, extracted_placeholders)
    
    ## Case 2:
    executable_path = configs_values.get("executables", {}).get(command_name)
    # Execute an executable defined inside a config file
    if executable_path:
        return executors.execute_config_application(executable_path, substitued_arguments, working_directories, extracted_placeholders)
    
    # Case 3:
    # Execute a globally callable executable
    # todo: Add a function that will check if the command is a globally callable command
    globall_callable_command = utilities.is_globally_callable_command(command_name)
    if globall_callable_command:
        # Treat as an external command to run in each folder
        return executors.execute_global_application(command_name, substitued_arguments, working_directories, extracted_placeholders)

    else:
        shell_command = utilities.get_shell_command(configs_values)
        return executors.execute_shell_command(command_name, substitued_arguments, shell_command, working_directories, extracted_placeholders)



if __name__ == "__main__":
    # This block runs only when the script is executed directly (e.g., python src/mate/main.py)
    # It adds the 'src' directory to the path to allow the 'mate' package to be found.
    # This is not needed when the package is installed.
    SRC_DIR = Path(__file__).resolve().parent.parent
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    sys.exit(main())


