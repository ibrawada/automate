import argparse
import copy
import importlib
import subprocess
import shutil
from pathlib import Path
from typing import Any

from mate import output, utilities
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
def execute_embedded_command(command_name: str, extracted_placeholders: dict, config_values: dict, working_dirs: list[str]) -> int:
    
    command_module = importlib.import_module(f".ops.{command_name}", package="mate")

    if not hasattr(command_module, "main"):
        output.error(f"No main() entry point for {command_module}")
        return globals.ERROR_CODE

    command_configs = config_values.get(command_name, {})

    for dir in working_dirs:
        subst_args = placeholderslib.substitute_placeholders(extracted_placeholders, config_values, Path(dir))
        
        parser = command_module.build_parser(
            argparse.ArgumentParser(prog=f"Nothing to say")
        )
        parsed_args = parser.parse_args(subst_args)
        
        output.info(f"{dir}> {command_name} {' '.join(subst_args)}")
        
        command_module.main(dir, parsed_args, command_configs)



# This runs the notepad (not python ops and not git)
def execute_config_application(application: str, placeholders: dict, config_values: dict, working_dirs: list[str]) -> int:
    for dir in working_dirs:        
        args = placeholderslib.substitute_placeholders(placeholders, config_values, Path(dir))
        run_application(application, [*args], working_dir=dir)



def execute_shell_command(shell_command: str, extracted_placeholders: dict, config_values: dict[str, Any], working_dirs: list[str]) -> int:
    shell_app_command = utilities.get_shell_app_cmd(config_values)
    
    if len(shell_app_command) == 0:
        output.error(f"No valid shell command provided. Provided was {shell_command}")
        globals.exit(globals.ERROR_CODE)

    shell_app_command.extend([shell_command])
    
    for current_dir in working_dirs:
        args = placeholderslib.substitute_placeholders(args, extracted_placeholders, Path(current_dir))
        shell_cmd = copy.deepcopy(shell_app_command)
        
        shell_cmd.extend(args)

        # print(f"shell_cmd: {shell_cmd}")

        output.info(f"{str(Path(current_dir).resolve())}> {' '.join(shell_cmd)}")

        execution_result = subprocess.run(shell_cmd, cwd=current_dir, capture_output=True, text=True)
        # TODO: Replace this with Error logging and implement --retry functionality
        # if execution_result.returncode != 0:
        #     return execution_result.returncode 
    return 0



def execute_global_application(application: str, placeholders: dict, config_values: dict[str, Any], working_dirs: list[str]) -> int:
    for dir in working_dirs:
        # args = utilities.substitute_local_variables(args, folders_vars[folder])
        args = placeholderslib.substitute_placeholders(placeholders, config_values, Path(dir))
        executation_state = run_application(application, args, working_dir=dir, check=False)
        # if executation_state != 0:
        #     return executation_state
    return 0