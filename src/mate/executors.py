import argparse
import copy
import importlib
import subprocess
import shutil
from pathlib import Path
from typing import Any

from mate import output, utilities
from mate import placeholderslib
from mate import globals

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
def execute_embedded_command(command_name: str, extracted_placeholders: dict, config_values: dict, working_dirs: list[str]) -> list[(str, int)]:
    
    command_module = importlib.import_module(f".ops.{command_name}", package="mate")

    if not hasattr(command_module, "main"):
        output.error(f"No main() entry point for {command_module}")
        globals.exit_mate(globals.ERROR_CODE)

    command_configs = config_values.get(command_name, {})

    ret_process_report = []
    for dir in working_dirs:
        subst_args = placeholderslib.substitute_placeholders(extracted_placeholders, config_values, Path(dir))
        
        parser = command_module.build_parser(
            argparse.ArgumentParser(prog=f"Nothing to say")
        )
        parsed_args = parser.parse_args(subst_args)
        
        output.info(f"{dir}> {command_name} {' '.join(subst_args)}")
        
        execution_status = command_module.main(dir, parsed_args, command_configs)
        ret_process_report.append((dir, execution_status))

    return ret_process_report



# This runs the notepad (not python ops and not git)
def execute_config_application(application: str, placeholders: dict, config_values: dict, working_dirs: list[str]) -> list[(str, int)]:
    ret_process_report = []
    for dir in working_dirs:        
        args = placeholderslib.substitute_placeholders(placeholders, config_values, Path(dir))
        execution_status = run_application(application, [*args], working_dir=dir)
        ret_process_report.append((dir, execution_status))

    return ret_process_report



def execute_shell_command(shell_command: str, extracted_placeholders: dict, config_values: dict[str, Any], working_dirs: list[str]) -> list[(str, int)]:
    shell_app_command = utilities.get_shell_app_cmd(config_values)
    
    if len(shell_app_command) == 0:
        output.error(f"No valid shell command provided. Provided was {shell_command}")
        globals.exit_mate(globals.ERROR_CODE)

    shell_app_command.extend([shell_command])

    ret_process_report = []

    for current_dir in working_dirs:
        args = placeholderslib.substitute_placeholders(args, extracted_placeholders, Path(current_dir))

        shell_cmd = copy.deepcopy(shell_app_command)
        shell_cmd.extend(args)

        output.info(f"{str(Path(current_dir).resolve())}> {' '.join(shell_cmd)}")
        execution_status = subprocess.run(shell_cmd, cwd=current_dir, capture_output=True, text=True)
        ret_process_report.append((dir, execution_status))

    return ret_process_report



def execute_global_application(application: str, placeholders: dict, config_values: dict[str, Any], working_dirs: list[str]) -> int:
    ret_process_report = []

    for dir in working_dirs:
        args = placeholderslib.substitute_placeholders(placeholders, config_values, Path(dir))
        execution_status = run_application(application, args, working_dir=dir, check=False)
        ret_process_report.append((dir, execution_status))

    return ret_process_report