#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path


from mate import output
from mate import placeholderslib
from mate.placeholderslib import Node
from mate import globals
from mate import executors
from mate import utilities
from mate.utilities import MateModule
from mate import config_handling



def create_command_parser(commands: dict[str, MateModule]):
    p = argparse.ArgumentParser(
        prog=f"python {Path(sys.argv[0]).name}",
        description="command runner",
        add_help=False,
    )
    command_names = []
    for name,_ in commands.items():
        command_names.append(name)

    p.add_argument("command", nargs="?", help=f"One of: {', '.join(sorted(command_names))}")
    p.add_argument("-sf", "--start-from", required=False, help="Set folder name from which the execution shall begin(or continue)")
    p.add_argument("-o", "--only", action="append", required=False, help="Set execution directory name. Only this one will be executed") # TODO, make it accept a csv list. Can also be populated with placeholders
    p.add_argument("-ef", "--exclude", action="append",
    default=[],
    help="Folders to exclude. Repeatable and/or comma-separated (e.g. --exclude=dir1,dir2 or --exclude dir1 --exclude dir2)",
)

    p.add_argument("-h", "--help", action="store_true", help="Show this help")

    return p


# Either prints a list of folder if no config name provided, else would also create/override an entry inside folders:<name>
def glob_folders(all_folders: list[str], modules: dict[str, MateModule], configs: dict, arguments: dict[str, list[Node]]) -> list[str]:

    ret_valid_dirs = []
    for dir in all_folders:
        for arg, pcs in arguments.items():
            placeholderslib.resolve_function_nodes(pcs, modules, Path(globals.get_workspace_dir()) / dir)
            if pcs[0].value == True:
                ret_valid_dirs.append(dir)

    return ret_valid_dirs



def main(cli_arguments=None):
    """Main command-line-interface entry point."""
    if cli_arguments is None:
        cli_arguments = sys.argv[1:]

    # --- Initial Setup: Parse only --wsd to set the context ---
    # This is required in order to define/locate the workspace directory and create/read according local-mate.conf file
    # Also this will remove --wsd and the <path> from the arguments list. This is helpful so that executors will not have to handle the wsd argument themselves
    wsd_parser = argparse.ArgumentParser(add_help=False)
    wsd_parser.add_argument("--wsd", type=Path, default=".")
    
    wsd_config_arg, command_arguments = wsd_parser.parse_known_args(cli_arguments)
    workspace_dir = wsd_config_arg.wsd
    globals.set_workspace_dir(workspace_dir)

    embedded_commands = utilities.collect_modules(Path(__file__).parent , globals.EMBEDDED_COMMANDS_FOLDER)
    placeholder_functions = utilities.collect_modules(Path(__file__).parent , globals.FUNCTIONS_FOLDER)
    
    utilities.load_modules(embedded_commands)
    utilities.load_modules(placeholder_functions)

    # Initialize config files is required
    config_handling.initialize_configfiles(embedded_commands)

    command_parser = create_command_parser(embedded_commands)
    command_arg, rest_arguments = command_parser.parse_known_args(command_arguments)

    if command_arg.command == "config":
        return config_handling.handle_config_arguments(command_arguments[1:])

    # REQ-###: System shall load global config file first followed by local config file
    # REQ-###: System shall override global config value by local config value if present in both files
    # Current behaviour will load the 
    configs_values = config_handling.read_configfiles([globals.get_global_configfile_path(), globals.get_local_configfile_path()])
    
    if command_arg.help and not command_arg.command:
        command_parser.print_help()
        return globals.SUCCESS_CODE
    
    if not command_arg.command:
        command_parser.error("a command is required.")
        return globals.ERROR_CODE

    
    # Extract placeholders for each independent argument
    arguments_and_placeholders = placeholderslib.extract_argument_placeholders(rest_arguments)
    
    # Resolve static placeholders (those that can be resolved from config values)
    for _, pcs in arguments_and_placeholders.items():
        if pcs == None:
            continue
        placeholderslib.resolve_config_nodes(pcs, configs_values)

    # Collect all folders in the workspace directory
    execution_directories_names = utilities.collect_folders(workspace_dir)
    # exclude those defined in the configs
    execution_directories_names = utilities.remove_folders(execution_directories_names, configs_values["folders"]["exclude"])


    if command_arg.command == "glob":
        folders = glob_folders(execution_directories_names, placeholder_functions, configs_values, arguments_and_placeholders)
        output.info(f"Use following argument: --only={','.join(folders)}")
        globals.exit_mate()
       

    # TODO: Extract folder handling into own function which can be tested without invoking full application

    ## Possible combinations
    # Overwrite collected directories if a "--only" list was provided
    # mate command --only=dir1,dir2
    # mate command --only=dir1,dir2 --start-from dir2 -> will skip dir 1 (useful for continue aborted/failed operation)
    # mate command --only=dir1,..,dirN --exclude=dir1,dir4,dir6 -> will remove dir1,dir4 and dir6 from execution list (useful for retry operation on folders that didn't succeed previously)
    if command_arg.only:
        execution_directories_names = utilities.split_csv_args(command_arg.only) # Todo: extract the function below into a free function. (Maybe this should be usable from within the arg parser)


    if command_arg.start_from:
        start_folder = command_arg.start_from
        execution_directories_names = utilities.remove_folders_until(execution_directories_names, start_folder)


    if command_arg.exclude:
        exclude_dirs = utilities.split_csv_args(command_arg.exclude)
        execution_directories_names = utilities.remove_folders(execution_directories_names, exclude_dirs)


    output.info(f"Execution on following folders:\n {', '.join(execution_directories_names)}\n")

    execution_directories_paths = []
    for dir in execution_directories_names:
        execution_directories_paths.append(Path(globals.get_workspace_dir()) / dir)


    ## Case 1:
    # Execute an embedded command (aka python script)
    command_name = command_arg.command 
    # if command_name in embedded_command_modules:
    if embedded_commands.get(command_name, {}):
        report = executors.execute_embedded_command(embedded_commands[command_name], arguments_and_placeholders, placeholder_functions, configs_values,  execution_directories_paths)
        output.status_report(report)
        output.suggest_retry(report)
        return globals.SUCCESS_CODE
    ## Case 2:
    executable_path = configs_values.get("executables", {}).get(command_name)
    # Execute an executable defined inside a config file
    if executable_path:
        report = executors.execute_config_application(executable_path, arguments_and_placeholders,placeholder_functions, configs_values, execution_directories_paths)
        output.status_report(report)
        output.suggest_retry(report)
        return globals.SUCCESS_CODE    
    # Case 3:
    # Execute a globally callable executable
    # todo: Add a function that will check if the command is a globally callable command
    is_globally_callable_application = utilities.is_callable_executable(command_name)
    if is_globally_callable_application:
        # Treat as an external command to run in each folder
        report = executors.execute_global_application(command_name, arguments_and_placeholders,placeholder_functions, configs_values, execution_directories_paths)
        output.status_report(report)
        output.suggest_retry(report)
        return globals.SUCCESS_CODE    
    # Case 4: Execute a possible shell command.
    else:
        report = executors.execute_shell_command(command_name, arguments_and_placeholders, placeholder_functions, configs_values, execution_directories_paths)
        output.status_report(report)
        output.suggest_retry(report)
        return globals.SUCCESS_CODE


if __name__ == "__main__":
    # This block runs only when the script is executed directly (e.g., python src/mate/main.py)
    # It adds the 'src' directory to the path to allow the 'mate' package to be found.
    # This is not needed when the package is installed.
    SRC_DIR = Path(__file__).resolve().parent.parent
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    sys.exit(main())


