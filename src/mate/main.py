#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
import importlib
from types import ModuleType

from mate.utilities import substitute_config_placeholders, extract_placeholders
from mate import config




def run_application(cmd: list[str], cwd: str | None = None, check: bool = True) -> int:
    dirname = Path(cwd).name
    print(f"({dirname}/) :> '{' '.join(cmd)}")

    try:
        completed = subprocess.run(cmd, cwd=cwd, check=check)
        return completed.returncode
    except FileNotFoundError as e:
        print(f"[mate] ERROR: command not found: {cmd[0]}\n{e}", file=sys.stderr)
        return 127
    except subprocess.CalledProcessError as e:
        return e.returncode




def execute_global_application(op_folders: list[str], args: list[str], folders_vars: dict) -> int:
    for folder in op_folders:
        args = substitute_local_variables(args, folders_vars[folder])
        run_application(args, cwd=folder, check=False)



# Todo: rename "ops" folder to commands
def collect_embedded_commands() -> list[str]:
    ops_directory = Path(__file__).parent / "ops"
    names = sorted(
        p.stem for p in ops_directory.glob("*.py") if p.stem != "__init__"
    )
    return names



# This runs the python operations (not git, or notepad)
def execute_embedded_command(command_name: str, command_arguments, command_configs: dict, folders: list[str],  folders_vars: dict) -> int:
    
    command_module = importlib.import_module(f".ops.{command_name}", package="mate")

    if not hasattr(command_module, "main"):
        print(f"Error no main entry point for {command_module}")
        sys.exit(1)

    for folder in folders:
        # per = _with(args, cwd=Path(folder))
        subst_args = substitute_local_variables(command_arguments, folders_vars[folder])
        parser = command_module.build_parser(
            # argparse.ArgumentParser(prog=f"{root_parser.prog} {root_args.command}")
            argparse.ArgumentParser(prog=f"Nothing to say")
        )
        parsed_args = parser.parse_args(subst_args)
        print(f"executing command {command_module.__name__}: {subst_args}")
        command_module.main(folder, parsed_args, command_configs)



# This runs the notepad (not python ops and not git)
def execute_config_application(folders: list[str], exe: str, args: list[str], folders_vars: dict) -> int:
    for folder in folders:        
        args = substitute_local_variables(args, folders_vars[folder])
        run_application([exe, *args], cwd=folder)



def collect_folders(working_dir: Path, exclude_folders: list[str]) -> list[str]:
    # iterate over cwd and collect only the direct folder in level 1

    ret_folders = []
    for wd_item in working_dir.iterdir():
        if any(ef in str(wd_item) for ef in exclude_folders):
            continue
        if wd_item.is_dir():
            ret_folders.append(str(wd_item))
    return ret_folders




# Todo: This will be remove and replaced by running operations
def create_local_variables(cwd: Path) -> dict:
    return {
        "folder_name": cwd.name
    }


# Todo: This will be remove and replaced by running operations
def substitute_local_variables(args, local_vars: dict) -> list[str]:
    substituted_args = []
    pattern = r"%(\w+)"  # matches %folder_name and captures "folder_name"
    def replace_placeholder(match):
        key = match.group(1)          # "folder_name"
        return local_vars.get(key, match[0])   # replace if found, otherwise keep original

    for arg in args:
        # Todo: startswith is wrong. because the variable could be part of a text example "something something %folder_name Seomthing"
        # I need a way to find %folder_name in the text, take it out and replace it with the correct value
        interpolated_arg = re.sub(pattern, replace_placeholder, arg)
        substituted_args.append(interpolated_arg)
    return substituted_args



def substitue_argument_placeholders_from_configs(args: list[str], configs: dict[str, list[str]]) -> list[str]:
    ret_substituted_arguments = []

    argument_placeholders = {}
    for arg in args:
        config_placeholders, function_placeholders = extract_placeholders(arg)
        argument_placeholders[arg]= {
                "config" : config_placeholders,
                "function" : function_placeholders
            }
        
    for argument, placeholders in argument_placeholders.items():
        config_placeholders = placeholders["config"]
        substituted_argument = substitute_config_placeholders(argument, config_placeholders, configs)
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
            command_module = load_embedded_command(command)
            config_values = command_module.get_default_config()
            modules_config.update(config_values)
        config.write_configfile(modules_config, config.get_global_configfile_path(), "a")



def make_root_parser(commands):
    p = argparse.ArgumentParser(
        prog=f"python {Path(sys.argv[0]).name}",
        description="command runner",
        add_help=False,
    )
    
    p.add_argument("command", nargs="?", help=f"One of: {', '.join(sorted(commands))}")
    # p.add_argument("--cwd", type=Path, default=Path.cwd(),
    #                help="Directory containing projects to operate on.")
    p.add_argument("--cwd", type=Path, default=".",
    # p.add_argument("--cwd", type=Path, default='E:/Gitea/_test_ProductsPipeline',
                   help="Directory containing projects to operate on.\nDefault is the current open directory")
    p.add_argument("-h", "--help", action="store_true", help="Show this help")

    
    return p



def cli(cli_arguments=None):
    """Main command-line-interface entry point."""
    if cli_arguments is None:
        cli_arguments = sys.argv[1:]

    # --- Initial Setup: Parse only --cwd to set the context ---
    # This is only required if the cwd is not the call directory
    cwd_parser = argparse.ArgumentParser(add_help=False)
    cwd_parser.add_argument("--cwd", type=Path, default=".")
    
    cwd_config_args, command_arguments = cwd_parser.parse_known_args(cli_arguments)
    config.set_cwd(cwd_config_args.cwd)



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
    

    # environment= configs.get("env", {})

    # Perform substitution on the raw argv before parsing
    # substituted_argv = substitute_placeholders(cli_arguments, configs)
    substitued_arguments = substitue_argument_placeholders_from_configs(command_arguments, configs_values)



    root_parser = make_root_parser(embedded_commands_names)
    root_args, rest_args = root_parser.parse_known_args(substitued_arguments)
    
    if root_args.help and not root_args.command:
        root_parser.print_help()
        return 0
    
    if not root_args.command:
        root_parser.error("a command is required.")
        return 1

    # working_directories = []
    # if configs_values["folders"].get("selection", ''):
    #     entry = configs_values["folders"]["selection"]
    #     selection = configs_values["folders"][entry]
    #     print(f"selection: {selection}")
    #     for folder in selection:
    #         working_directories.append(str(Path(root_args.cwd, folder)))
    # else:
    working_directories = collect_folders(root_args.cwd, configs_values["folders"]["exclude"])
    
    print("folder: ", working_directories)

    # Create variables that are local to a folder
    # ATM only folder_name is created
    folder_local_vars = {}
    for folder in working_directories:
        folder_local_vars[folder] = create_local_variables(Path(folder))
        
    # Execute an embedded command (aka python script)
    if root_args.command in embedded_commands_names:
        return execute_embedded_command(root_args.command, rest_args, configs_values.get(root_args.command, {}), working_directories, folder_local_vars)
    
    executable_path = configs_values.get("executables", {}).get(root_args.command)
    # Execute an executable defined inside a config file
    if executable_path:
        return execute_config_application(working_directories, executable_path, rest_args, folder_local_vars)
    # Execute a globally callable executable
    else:
        # Treat as an external command to run in each folder
        return execute_global_application(working_directories, substitued_arguments, folder_local_vars)
        # return direct_call(folders, [root_args.command, *rest_args])


if __name__ == "__main__":
    # This block runs only when the script is executed directly (e.g., python src/mate/main.py)
    # It adds the 'src' directory to the path to allow the 'mate' package to be found.
    # This is not needed when the package is installed.
    SRC_DIR = Path(__file__).resolve().parent.parent
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    sys.exit(cli())


#