import argparse
import copy
import importlib
import subprocess
import shutil
from pathlib import Path

from mate import output
from mate import placeholderslib


def run_application(application: str, cmd: list[str], working_dir: str, check: bool = True) -> int:
    full_cmd = [application]
    full_cmd.extend(cmd)

    output.info(f"{str(Path(working_dir).resolve())}> {' '.join(full_cmd)}")

    try:
        completed = subprocess.run(full_cmd, cwd=working_dir, check=check)
        return completed.returncode
    except FileNotFoundError as e:
        output.error(f"command not found: {full_cmd[0]}\n{e}")
        return globals.ERROR_CODE
    except subprocess.CalledProcessError as e:
        return e.returncode


# This runs the python operations (not git, or notepad)
def execute_embedded_command(command_name: str, command_arguments, command_configs: dict, working_dirs: list[str],  placeholders: dict) -> int:
    
    command_module = importlib.import_module(f".ops.{command_name}", package="mate")

    if not hasattr(command_module, "main"):
        output.error(f"No main() entry point for {command_module}")
        return globals.ERROR_CODE

    for dir in working_dirs:
        subst_args = placeholderslib.substitute_arguments_function_placeholders(command_arguments, placeholders, Path(dir))
        
        parser = command_module.build_parser(
            argparse.ArgumentParser(prog=f"Nothing to say")
        )
        parsed_args = parser.parse_args(subst_args)
        
        output.info(f"executing command {command_name}: {subst_args}")
        
        command_module.main(dir, parsed_args, command_configs)



# This runs the notepad (not python ops and not git)
def execute_config_application(application: str, args: list[str], working_dirs: list[str], placeholders: dict) -> int:
    for dir in working_dirs:        
        args = placeholderslib.substitute_arguments_function_placeholders(args, placeholders, dir)
        run_application(application, [*args], working_dir=dir)



def execute_shell_command(application: str, args: list[str], shell_command: list[str], working_dirs: list[str], placeholders: dict) -> int:
    full_cmd = shell_command
    full_cmd.extend([application])
    
    if len(shell_command) == 0:
        output.error("No shell command provided")
        globals.exit(globals.ERROR_CODE)
    
    for current_dir in working_dirs:
        args = placeholders.substitute_arguments_function_placeholders(args, placeholders, Path(current_dir))
        shell_cmd = copy.deepcopy(full_cmd)
        
        shell_cmd.extend(args)

        print(f"shell_cmd: {shell_cmd}")

        output.info(f"{str(Path(current_dir).resolve())}> {' '.join(shell_cmd)}")

        execution_result = subprocess.run(shell_cmd, cwd=current_dir, capture_output=True, text=True)
        # TODO: Replace this with Error logging and implement --retry functionality
        # if execution_result.returncode != 0:
        #     return execution_result.returncode 
    return 0



def execute_global_application(application: str, args: list[str], working_dirs: list[str], placeholders: dict) -> int:
    for dir in working_dirs:
        # args = utilities.substitute_local_variables(args, folders_vars[folder])
        args = placeholderslib.substitute_arguments_function_placeholders(args, placeholders, Path(dir))
        executation_state = run_application(application, args, working_dir=dir, check=False)
        # if executation_state != 0:
        #     return executation_state
    return 0