import argparse
import importlib
import subprocess
import shutil
from pathlib import Path
from typing import Any

from mate import output, utilities
from mate.utilities import MateModule
from mate import placeholderslib
from mate.placeholderslib import Node
from mate import globals


def resolve_cli_args(arguments_and_placeholders: dict[str, list[Node]], placeholder_functions: dict[str, MateModule], working_dir: Path) -> list[str]:
    subst_args = []
    for arg, pcs in arguments_and_placeholders.items():
        if  pcs:
            placeholderslib.resolve_function_nodes(pcs, placeholder_functions, working_dir)
            arg_value = placeholderslib.resolve_argument(arg, pcs)
            subst_args.append(arg_value)
        else:
            subst_args.append(arg)
    return subst_args



def run_application(application: str, cmd: list[str], working_dir: Path, check: bool = True) -> int:
    full_cmd = [application]
    full_cmd.extend(cmd)

    output.info(f"{str(working_dir.resolve())}> {' '.join(full_cmd)}")

    try:
        completed = subprocess.run(full_cmd, cwd=working_dir, check=check)
        return completed.returncode
    except FileNotFoundError as e:
        output.error(f"command not found: {full_cmd[0]}\n{e}")
        return globals.ERROR_CODE
    except subprocess.CalledProcessError as e:
        return e.returncode


# This runs the python operations (not git, or notepad)
def execute_embedded_command(command_module: MateModule, arguments_and_placeholders: dict[str, list[Node]], placeholder_functions: dict[str, MateModule], config_values: dict[str, Any], working_dirs: list[Path]) -> list[(str, int)]:
    module = command_module.module
    if not hasattr(module, "main"):
        output.error(f"No main() entry point for {command_module}")
        globals.exit_mate(globals.ERROR_CODE)

    command_configs = config_values.get(command_module.path, {})

    ret_process_report = []
    for dir in working_dirs:
        subst_args = resolve_cli_args(arguments_and_placeholders, placeholder_functions, dir)
        
        parser = module.build_parser(
            argparse.ArgumentParser(prog=f"Help for {command_module.path}")
        )
        parsed_args = parser.parse_args(subst_args)
        
        output.info(f"{dir}> {command_module.path} {' '.join(subst_args)}")
        
        execution_status = module.main(dir, parsed_args, command_configs)
        ret_process_report.append((str(dir), execution_status))

    return ret_process_report



# This runs the notepad (not python ops and not git)
def execute_config_application(application: str, arguments_and_placeholders: dict[str, list[Node]], placeholder_functions: dict[str, MateModule], config_values: dict[str, Any], working_dirs: list[Path]) -> list[(str, int)]:
    ret_process_report = []
    for dir in working_dirs:        
        subst_args = resolve_cli_args(arguments_and_placeholders, placeholder_functions, dir)
        execution_status = run_application(application, [*subst_args], working_dir=dir)
        ret_process_report.append((str(dir), execution_status))

    return ret_process_report



def execute_shell_command(shell_command: str, arguments_and_placeholders: dict[str, list[Node]],placeholder_functions: dict[str, MateModule], config_values: dict[str, Any], working_dirs: list[Path]) -> list[tuple[str, int]]:
    shell_app_command = utilities.get_shell_app_cmd(config_values)
    shell_app = shell_app_command[0]

    ret_process_report = []

    for current_dir in working_dirs:
        subst_args = resolve_cli_args(arguments_and_placeholders, placeholder_functions, current_dir)

        # The shell takes the whole command as one string; extra argv items would not be part of it (e.g. bash -c)
        command_line = utilities.build_shell_command_line(shell_app, shell_command, subst_args)
        shell_cmd = [*shell_app_command, command_line]

        output.info(f"{str(Path(current_dir).resolve())}> {command_line}")
        try:
            run_status = subprocess.run(shell_cmd, cwd=current_dir, text=True)
            ret_process_report.append((str(current_dir), run_status.returncode))
        except OSError as e:
            output.error(f"Failed to run shell {shell_app}: {e}")
            ret_process_report.append((str(current_dir), globals.ERROR_CODE))

    return ret_process_report



def execute_global_application(application: str, arguments_and_placeholders: dict[str, list[Node]],placeholder_functions: dict[str, MateModule], config_values: dict[str, Any], working_dirs: list[Path]) -> int:
    ret_process_report = []

    for dir in working_dirs:
        subst_args = resolve_cli_args(arguments_and_placeholders, placeholder_functions, dir)
        execution_status = run_application(application, subst_args, working_dir=dir, check=False)
        ret_process_report.append((str(dir), execution_status))

    return ret_process_report