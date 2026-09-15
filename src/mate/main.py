#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path
import importlib


from mate import output
from mate import placeholderslib
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
    p.add_argument("-sf", "--start-from", required=False, help="Set folder name from which the execution shall begin(or continue)")
    p.add_argument("-o", "--only", action="append", required=False, help="Set working directory name. Only this one will be executed") # TODO, make it accept a csv list. Can also be populated with placeholders
    p.add_argument("-ef", "--exclude", action="append",
    default=[],
    help="Folders to exclude. Repeatable and/or comma-separated (e.g. --exclude=dir1,dir2 or --exclude dir1 --exclude dir2)",
)

    p.add_argument("-h", "--help", action="store_true", help="Show this help")

    return p


# Either prints a list of folder if no config name provided, else would also create/override an entry inside folders:<name>
def glob_folders(all_folders: list[str], arguments: list[str]) -> list[str]:
    # Need to first parse the arguments to determine what is required.
    # Check if the argument for config name provided.
    p = argparse.ArgumentParser(prog=f"",description="", add_help=False)    
    p.add_argument("condition", nargs="?", help=f"")
    p.add_argument("--name", required=False, help="Set name for the config folder:<name> entry")
    parsed_args, rest_args = p.parse_known_args(arguments)

    # Parse placeholder condition. and resolve the value immediately
    placeholders = placeholderslib.extract_argument_placeholders([parsed_args.condition])

    
    condition_root, condition_name = str(parsed_args.condition).removeprefix('%').removesuffix('%').split('/')
    condition_name = condition_name.removesuffix('[]')
    condition_module = importlib.import_module(f".conditions.{condition_root}.{condition_name}", package="mate")

    ret_valid_dirs = []
    for dir in all_folders:
        condition_status = condition_module.run(Path(globals.get_cwd() / dir), rest_args)
        if condition_status:
            ret_valid_dirs.append(dir)

    return ret_valid_dirs



def main(cli_arguments=None):
    """Main command-line-interface entry point."""
    if cli_arguments is None:
        cli_arguments = sys.argv[1:]

    # --- Initial Setup: Parse only --cwd to set the context ---
    # This is required in order to define/locate the current working directory and create/read according local-mate.conf file
    # Also this will remove --cwd and the <path> from the arguments list. This is helpful so that executors will not have to handle the cwd argument themselves
    cwd_parser = argparse.ArgumentParser(add_help=False)
    cwd_parser.add_argument("--cwd", type=Path, default=".")
    
    cwd_config_arg, command_arguments = cwd_parser.parse_known_args(cli_arguments)
    current_working_dir = cwd_config_arg.cwd
    globals.set_cwd(current_working_dir)

    embedded_commands_names = utilities.collect_embedded_commands(Path(__file__).parent / globals.EMBEDDED_COMMANDS_FOLDER)
    
    # Initialize config files is required
    config_handling.initialize_configfiles(embedded_commands_names)

    command_parser = create_command_parser(embedded_commands_names)
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

    
    arguments_and_placeholders = placeholderslib.extract_argument_placeholders(rest_arguments)



    # Collect all folders in the working directory
    working_directories = utilities.collect_folders(current_working_dir)
    # exclude those defined in the configs
    working_directories = utilities.remove_folders(working_directories, configs_values["folders"]["exclude"])


    if command_arg.command == "glob":
        folders = glob_folders(working_directories, command_arguments[1:])
        output.info(f"Use following argument: --only={','.join(folders)}")
        globals.exit_mate()
       

    # TODO: Extract folder handling into own function which can be tested without invoking full application

    ## Possible combinations
    # Overwrite collected directories if a "--only" list was provided
    # mate command --only=dir1,dir2
    # mate command --only=dir1,dir2 --start-from dir2 -> will skip dir 1 (useful for continue aborted/failed operation)
    # mate command --only=dir1,..,dirN --exclude=dir1,dir4,dir6 -> will remove dir1,dir4 and dir6 from execution list (useful for retry operation on folders that didn't succeed previously)
    if command_arg.only:
        working_directories = utilities.split_csv_args(command_arg.only) # Todo: extract the function below into a free function. (Maybe this should be usable from within the arg parser)


    if command_arg.start_from:
        start_folder = command_arg.start_from
        working_directories = utilities.remove_folders_until(working_directories, start_folder)


    if command_arg.exclude:
        exclude_dirs = utilities.split_csv_args(command_arg.exclude)
        working_directories = utilities.remove_folders(working_directories, exclude_dirs)




    output.info(f"Execution on following folders:\n {', '.join(working_directories)}\n")
    
    ## Case 1:
    # Execute an embedded command (aka python script)
    command_name = command_arg.command 
    if command_name in embedded_commands_names:
        report = executors.execute_embedded_command(command_name, arguments_and_placeholders, configs_values, working_directories)
        output.status_report(report)
        return globals.SUCCESS_CODE
    ## Case 2:
    executable_path = configs_values.get("executables", {}).get(command_name)
    # Execute an executable defined inside a config file
    if executable_path:
        report = executors.execute_config_application(executable_path, arguments_and_placeholders, configs_values, working_directories)
        output.status_report(report)
        return globals.SUCCESS_CODE    
    # Case 3:
    # Execute a globally callable executable
    # todo: Add a function that will check if the command is a globally callable command
    is_globally_callable_application = utilities.is_globally_callable_command(command_name)
    if is_globally_callable_application:
        # Treat as an external command to run in each folder
        report = executors.execute_global_application(command_name, arguments_and_placeholders, configs_values, working_directories)
        output.status_report(report)
        return globals.SUCCESS_CODE    
    # Case 4: Execute a possible shell command.
    else:
        report = executors.execute_shell_command(command_name, arguments_and_placeholders, configs_values, working_directories)
        output.status_report(report)
        return globals.SUCCESS_CODE


if __name__ == "__main__":
    # This block runs only when the script is executed directly (e.g., python src/mate/main.py)
    # It adds the 'src' directory to the path to allow the 'mate' package to be found.
    # This is not needed when the package is installed.
    SRC_DIR = Path(__file__).resolve().parent.parent
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    sys.exit(main())


