#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
import importlib
from types import ModuleType
import copy

from mate import utilities
from mate import config
from mate import output

ERROR_CODE = 127



def run_application(application: str, cmd: list[str], working_dir: str, check: bool = True) -> int:
    full_cmd = [application]
    full_cmd.extend(cmd)

    output.info(f"{str(Path(working_dir).resolve())}> {' '.join(full_cmd)}")

    try:
        completed = subprocess.run(full_cmd, cwd=working_dir, check=check)
        return completed.returncode
    except FileNotFoundError as e:
        output.error(f"command not found: {full_cmd[0]}\n{e}")
        return ERROR_CODE
    except subprocess.CalledProcessError as e:
        return e.returncode



def execute_global_application(application: str, args: list[str], working_dirs: list[str], placeholders: dict) -> int:
    for dir in working_dirs:
        # args = utilities.substitute_local_variables(args, folders_vars[folder])
        args = substitute_arguments_function_placeholders(args, placeholders, Path(dir))
        executation_state = run_application(application, args, working_dir=dir, check=False)
        if executation_state != 0:
            return executation_state
    return 0



def is_globally_callable_command(command_name: str) -> bool:
    return shutil.which(command_name) != None


def get_shell_command(configs: dict) -> list[str]:    
    if sys.platform.startswith("win"):
        shell_app = configs["shell"]["windows"]
        return [shell_app, "-NoProfile", "-Command"]
    
    elif sys.platform.startswith("linux"):
        shell_app = configs["shell"]["linux"]
        return [shell_app, "-c"]
    else:
        output.error("No shell application defined")
        return []
    

def execute_shell_command(application: str, args: list[str], shell_command: list[str], working_dirs: list[str], placeholders: dict) -> int:
    full_cmd = shell_command
    full_cmd.extend([application])
    
    if len(shell_command) == 0:
        output.error("No shell command provided")
        return ERROR_CODE
    
    for current_dir in working_dirs:
        args = substitute_arguments_function_placeholders(args, placeholders, Path(current_dir))
        shell_cmd = copy.deepcopy(full_cmd)
        
        shell_cmd.extend(args)

        print(f"shell_cmd: {shell_cmd}")

        output.info(f"{str(Path(current_dir).resolve())}> {' '.join(shell_cmd)}")

        execution_result = subprocess.run(shell_cmd, cwd=current_dir, capture_output=True, text=True)
        if execution_result.returncode != 0:
            return execution_result.returncode 
    return 0



# Todo: rename "ops" folder to commands
def collect_embedded_commands() -> list[str]:
    ops_directory = Path(__file__).parent / "ops"
    names = sorted(
        p.stem for p in ops_directory.glob("*.py") if p.stem != "__init__"
    )
    return names



# This runs the python operations (not git, or notepad)
def execute_embedded_command(command_name: str, command_arguments, command_configs: dict, working_dirs: list[str],  placeholders: dict) -> int:
    
    command_module = importlib.import_module(f".ops.{command_name}", package="mate")

    if not hasattr(command_module, "main"):
        output.error(f"No main() entry point for {command_module}")
        return ERROR_CODE

    for dir in working_dirs:
        subst_args = substitute_arguments_function_placeholders(command_arguments, placeholders, Path(dir))
        
        parser = command_module.build_parser(
            argparse.ArgumentParser(prog=f"Nothing to say")
        )
        parsed_args = parser.parse_args(subst_args)
        
        output.info(f"executing command {command_name}: {subst_args}")
        
        command_module.main(dir, parsed_args, command_configs)



# This runs the notepad (not python ops and not git)
def execute_config_application(application: str, args: list[str], working_dirs: list[str], placeholders: dict) -> int:
    for dir in working_dirs:        
        args = substitute_arguments_function_placeholders(args, placeholders, dir)
        run_application([application, *args], dir)



def collect_folders(main_directory: Path, exclude_folders: list[str]) -> list[str]:
    # iterate over cwd and collect only the direct folder in level 1
    ret_folders = []
    for child_item in main_directory.iterdir():
        if any(ef in str(child_item) for ef in exclude_folders):
            continue
        if child_item.is_dir():
            ret_folders.append(str(child_item))
    return ret_folders



def extract_argument_placeholders(arguments: list[str]) -> dict:
    argument_placeholders = {}
    for arg in arguments:
        config_placeholders, function_placeholders = utilities.extract_placeholders(arg)
        argument_placeholders[arg]= {
                "config" : config_placeholders,
                "function" : function_placeholders
            }
        
    return argument_placeholders



def substitute_arguments_function_placeholders(args: list[str], arg_placeholders: dict, working_dir: Path) -> list[str]:
    ret_substituted_arguments = []
        
    for argument, placeholders in arg_placeholders.items():
        function_placeholders = placeholders["function"]
        substituted_argument = utilities.substitute_function_placeholders(argument, function_placeholders, working_dir)
        ret_substituted_arguments.append(substituted_argument)

    return ret_substituted_arguments    



def substitute_argument_placeholders_from_configs(args: list[str], argument_placeholders: dict, configs: dict[str, dict[str, str]]) -> list[str]:
    ret_substituted_arguments = []
        
    for argument, placeholders in argument_placeholders.items():
        config_placeholders = placeholders["config"]
        substituted_argument = utilities.substitute_config_placeholders(argument, config_placeholders, configs)
        ret_substituted_arguments.append(substituted_argument)

    return ret_substituted_arguments



def initialize_configfiles(command_names: list[str]):    
    config_path = config.get_global_configfile_path()
    global_config_created = config.create_configfile_if_none(config_path, config.DEFAULT_GLOBAL_CONFIG_CONTENT)
    
    config_path = config.get_local_configfile_path()
    config.create_configfile_if_none(config_path, config.DEFAULT_LOCAL_CONFIG_CONTENT)    

    if global_config_created:
        # For each command write config file default values if nothing yet present
        modules_config = {}
        for command in command_names:
            command_module = importlib.import_module(f".ops.{command}", package="mate")
            config_values = command_module.get_default_config()
            modules_config.update(config_values)
        config.write_configfile(modules_config, config.get_global_configfile_path(), "a")



def create_command_parser(commands):
    p = argparse.ArgumentParser(
        prog=f"python {Path(sys.argv[0]).name}",
        description="command runner",
        add_help=False,
    )
    
    p.add_argument("command", nargs="?", help=f"One of: {', '.join(sorted(commands))}")
    p.add_argument("-h", "--help", action="store_true", help="Show this help")

    return p



def cli(cli_arguments=None):
    """Main command-line-interface entry point."""
    if cli_arguments is None:
        cli_arguments = sys.argv[1:]

    # --- Initial Setup: Parse only --cwd to set the context ---
    # This is required in order to define/locate the current working directory and create/read according local-mate.conf file
    cwd_parser = argparse.ArgumentParser(add_help=False)
    cwd_parser.add_argument("--cwd", type=Path, default=".")
    
    cwd_config_arg, command_arguments = cwd_parser.parse_known_args(cli_arguments)
    current_working_dir = cwd_config_arg.cwd
    config.set_cwd(current_working_dir)

    embedded_commands_names = collect_embedded_commands()
    
    # Initialize config files is required
    initialize_configfiles(embedded_commands_names)

    # Check if command_arguments contains "config" instead of actual command (eg. [config, var:test=test])
    # - has length more than 2 elements -> user provided a value to be modified
    # - and if the 0th element is actually config -> only then update configs
    if len(command_arguments) >= 2 and command_arguments[0] == "config":
        # Provide only the config content to be update (strip the "config" from the list)
        return config.handle_config_arguments(command_arguments[1:])
        

    # REQ-###: System shall load global config file first followed by local config file
    # REQ-###: System shall override global config value by local config value if present in both files
    # Current behaviour will load the 
    configs_values = config.read_configfiles([config.get_global_configfile_path(), config.get_local_configfile_path()])

    command_parser = create_command_parser(embedded_commands_names)
    command_arg, rest_arguments = command_parser.parse_known_args(command_arguments)
    
    if command_arg.help and not command_arg.command:
        command_parser.print_help()
        return 0
    
    if not command_arg.command:
        command_parser.error("a command is required.")
        return 1

    working_directories = collect_folders(current_working_dir, configs_values["folders"]["exclude"])


    extracted_placeholders = extract_argument_placeholders(rest_arguments)
    substitued_arguments = substitute_argument_placeholders_from_configs(rest_arguments, extracted_placeholders, configs_values)

    ## Case 1:
    # Execute an embedded command (aka python script)
    command_name = command_arg.command 
    if command_name in embedded_commands_names:
        return execute_embedded_command(command_name, substitued_arguments, configs_values.get(command_name, {}), working_directories, extracted_placeholders)
    
    ## Case 2:
    executable_path = configs_values.get("executables", {}).get(command_name)
    # Execute an executable defined inside a config file
    if executable_path:
        return execute_config_application(executable_path, substitued_arguments, working_directories, extracted_placeholders)
    
    # Case 3:
    # Execute a globally callable executable
    # todo: Add a function that will check if the command is a globally callable command
    globall_callable_command = is_globally_callable_command(command_name)
    if globall_callable_command:
        # Treat as an external command to run in each folder
        return execute_global_application(command_name, substitued_arguments, working_directories, extracted_placeholders)

    else:
        shell_command = get_shell_command(configs_values)
        return execute_shell_command(command_name, substitued_arguments, shell_command, working_directories, extracted_placeholders)



if __name__ == "__main__":
    # This block runs only when the script is executed directly (e.g., python src/mate/main.py)
    # It adds the 'src' directory to the path to allow the 'mate' package to be found.
    # This is not needed when the package is installed.
    SRC_DIR = Path(__file__).resolve().parent.parent
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    sys.exit(cli())


