import argparse

import subprocess

from pathlib import Path
from typing import Any

from mate import output, utilities
from mate.utilities import MateModule
from mate import placeholderslib
from mate.placeholderslib import Node
from mate import globals


from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import subprocess
import sys
import threading


class ExecutorType(Enum):
    APPLICATION = "application"
    SHELL = "shell"
    EMBEDDED = "embedded"


@dataclass
class ExecutionResult:
    command_name: str
    command_args: list[str]
    cwd: Path
    executor: ExecutorType

    returncode: int
    stdout: str = ""
    stderr: str = ""
    exception: Exception | None = None

    @property
    def succeeded(self) -> bool:
        return self.exception is None and self.returncode == 0




def resolve_cli_args(arguments_and_placeholders: dict[str, list[Node]], 
                     placeholder_functions: dict[str, MateModule], 
                     execution_dir: Path) -> list[str]:
    
    subst_args = []
    for arg, pcs in arguments_and_placeholders.items():
        if  pcs:
            placeholderslib.resolve_function_nodes(pcs, placeholder_functions, execution_dir)
            arg_value = placeholderslib.resolve_argument(arg, pcs)
            subst_args.append(arg_value)
        else:
            subst_args.append(arg)
    return subst_args



def run_application(
    application: str,
    arguments: list[str],
    execution_dir: Path,
    live_output: bool = True,
) -> ExecutionResult:

    full_cmd = [application, *arguments]

    output.info(
        f"{execution_dir.resolve()}> {' '.join(full_cmd)}"
    )

    try:
        process = subprocess.Popen(
            full_cmd,
            cwd=execution_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors="replace",
            bufsize=1,
        )

        stdout_lines: list[str] = []
        stderr_lines: list[str] = []

        def read_stream(stream, collected, target):
            for line in iter(stream.readline, ""):
                collected.append(line)

                if live_output:
                    print(line, end="", file=target, flush=True)

            stream.close()

        stdout_thread = threading.Thread(
            target=read_stream,
            args=(process.stdout, stdout_lines, sys.stdout),
        )

        stderr_thread = threading.Thread(
            target=read_stream,
            args=(process.stderr, stderr_lines, sys.stderr),
        )

        stdout_thread.start()
        stderr_thread.start()

        returncode = process.wait()

        stdout_thread.join()
        stderr_thread.join()

        return ExecutionResult(
            command_name=application,
            command_args=arguments,
            cwd=execution_dir,
            executor=ExecutorType.APPLICATION,
            returncode=returncode,
            stdout="".join(stdout_lines),
            stderr="".join(stderr_lines),
        )

    except OSError as e:
        output.error(f"command not found: {application}\n{e}")
        return ExecutionResult(
            command_name=application,
            command_args=arguments,
            cwd=execution_dir,
            executor=ExecutorType.APPLICATION,
            returncode=globals.ERROR_CODE,
            stderr=str(e),
            exception=e,
        )



# # Embedded commands do not stream their output, so it is printed once they return
# def report_embedded_result(result: ExecutionResult):
#     if result.stdout:
#         output.info(result.stdout)
#     if result.stderr:
#         if result.returncode == globals.WARNING_CODE:
#             output.warning(result.stderr)
#         else:
#             output.error(result.stderr)



# This runs the python operations (not git, or notepad)
def execute_embedded_command(command_module: MateModule, arguments_and_placeholders: dict[str, list[Node]], 
                             placeholder_functions: dict[str, MateModule], config_values: dict[str, Any], 
                             execution_dirs: list[Path]) -> list[ExecutionResult]:
    module = command_module.module
    if not hasattr(module, "main"):
        globals.exit_mate(globals.ERROR_CODE, f"No main() entry point for {command_module}")

    command_configs = config_values.get(command_module.name, {})

    ret_process_report = []
    for dir in execution_dirs:
        subst_args = resolve_cli_args(arguments_and_placeholders, placeholder_functions, dir)
        
        parser = module.build_parser(
            argparse.ArgumentParser(prog=f"Help for {command_module.name}")
        )
        parsed_args = parser.parse_args(subst_args)
        
        output.info(f"{dir}> {command_module.name} {' '.join(subst_args)}")
        
        execution_status = module.main(dir, parsed_args, command_configs)

        ret_process_report.append(execution_status)

    return ret_process_report



# This runs the notepad (not python ops and not git)
def execute_config_application(application: str, arguments_and_placeholders: dict[str, list[Node]], 
                               placeholder_functions: dict[str, MateModule], config_values: dict[str, Any], 
                               execution_dirs: list[Path]) -> list[ExecutionResult]:
    ret_process_report = []
    for dir in execution_dirs:        
        subst_args = resolve_cli_args(arguments_and_placeholders, placeholder_functions, dir)
        execution_status = run_application(application, [*subst_args], execution_dir=dir)

        ret_process_report.append(execution_status)

    return ret_process_report



def execute_shell_command(shell_command: str, arguments_and_placeholders: dict[str, list[Node]], 
                          placeholder_functions: dict[str, MateModule], config_values: dict[str, Any], 
                          execution_dirs: list[Path]) -> list[tuple[str, ExecutionResult]]:
    
    shell_app_name = utilities.get_shell_app_cmd(config_values) # eg = powershell
    shell_app_arguments = utilities.get_shell_app_arguments(shell_app_name) # eg = -NoProfile -Command

    ret_process_report = []

    for current_dir in execution_dirs:
        subst_args = resolve_cli_args(arguments_and_placeholders, placeholder_functions, current_dir)

        # The shell takes the whole command as one string; extra argv items would not be part of it (e.g. bash -c)
        command_line = utilities.build_shell_command_line(shell_app_name, shell_command, subst_args)
        shell_cmd = [*shell_app_arguments, command_line]


        execution_status = run_application(shell_app_name, shell_cmd, current_dir)
        ret_process_report.append(execution_status)

    return ret_process_report



def execute_global_application(application: str, arguments_and_placeholders: dict[str, list[Node]], 
                               placeholder_functions: dict[str, MateModule], config_values: dict[str, Any], 
                               execution_dirs: list[Path]) -> list[ExecutionResult]:
    ret_process_report = []

    for dir in execution_dirs:
        subst_args = resolve_cli_args(arguments_and_placeholders, placeholder_functions, dir)
        execution_status = run_application(application, subst_args, execution_dir=dir)

        ret_process_report.append(execution_status)

    return ret_process_report