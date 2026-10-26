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
    command: list[str]
    cwd: Path
    executor: ExecutorType

    returncode: int
    stdout: str = ""
    stderr: str = ""
    exception: Exception | None = None

    @property
    def succeeded(self) -> bool:
        return self.exception is None and self.returncode == 0




def resolve_cli_args(arguments_and_placeholders: dict[str, list[Node]], placeholder_functions: dict[str, MateModule], execution_dir: Path) -> list[str]:
    subst_args = []
    for arg, pcs in arguments_and_placeholders.items():
        if  pcs:
            placeholderslib.resolve_function_nodes(pcs, placeholder_functions, execution_dir)
            arg_value = placeholderslib.resolve_argument(arg, pcs)
            subst_args.append(arg_value)
        else:
            subst_args.append(arg)
    return subst_args



# def run_application(application: str, cmd: list[str], execution_dir: Path, check: bool = True) -> int:
#     full_cmd = [application]
#     full_cmd.extend(cmd)

#     output.info(f"{str(execution_dir.resolve())}> {' '.join(full_cmd)}")

#     try:
#         completed = subprocess.run(full_cmd, cwd=execution_dir, check=check)
#         return completed.returncode
#     except FileNotFoundError as e:
#         output.error(f"command not found: {full_cmd[0]}\n{e}")
#         return globals.ERROR_CODE
#     except subprocess.CalledProcessError as e:
#         return e.returncode




def run_application(
    application: str,
    cmd: list[str],
    execution_dir: Path,
    live_output: bool = True,
) -> ExecutionResult:

    full_cmd = [application, *cmd]

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
            command=full_cmd, # Split into command name and arguments
            cwd=execution_dir,
            executor=ExecutorType.APPLICATION,
            returncode=returncode,
            stdout="".join(stdout_lines),
            stderr="".join(stderr_lines),
        )

    except OSError as e:
        return ExecutionResult(
            command=full_cmd,
            cwd=execution_dir,
            executor=ExecutorType.APPLICATION,
            returncode=globals.ERROR_CODE,
            stderr=str(e),
            exception=e,
        )



# This runs the python operations (not git, or notepad)
def execute_embedded_command(command_module: MateModule, arguments_and_placeholders: dict[str, list[Node]], placeholder_functions: dict[str, MateModule], config_values: dict[str, Any], execution_dirs: list[Path]) -> list[(str, int)]:
    module = command_module.module
    if not hasattr(module, "main"):
        output.error(f"No main() entry point for {command_module}")
        globals.exit_mate(globals.ERROR_CODE)

    command_configs = config_values.get(command_module.name, {})

    print(f"command configs: {command_configs}")

    ret_process_report = []
    for dir in execution_dirs:
        subst_args = resolve_cli_args(arguments_and_placeholders, placeholder_functions, dir)
        
        parser = module.build_parser(
            argparse.ArgumentParser(prog=f"Help for {command_module.name}")
        )
        parsed_args = parser.parse_args(subst_args)
        
        output.info(f"{dir}> {command_module.name} {' '.join(subst_args)}")
        
        execution_status = module.main(dir, parsed_args, command_configs)
        ret_process_report.append((str(dir), execution_status))

    return ret_process_report



# This runs the notepad (not python ops and not git)
def execute_config_application(application: str, arguments_and_placeholders: dict[str, list[Node]], placeholder_functions: dict[str, MateModule], config_values: dict[str, Any], execution_dirs: list[Path]) -> list[(str, int)]:
    ret_process_report = []
    for dir in execution_dirs:        
        subst_args = resolve_cli_args(arguments_and_placeholders, placeholder_functions, dir)
        execution_status = run_application(application, [*subst_args], execution_dir=dir)
        ret_process_report.append((str(dir), execution_status))

    return ret_process_report



def execute_shell_command(shell_command: str, arguments_and_placeholders: dict[str, list[Node]],placeholder_functions: dict[str, MateModule], config_values: dict[str, Any], execution_dirs: list[Path]) -> list[tuple[str, int]]:
    shell_app_command = utilities.get_shell_app_cmd(config_values)
    shell_app = shell_app_command[0]

    ret_process_report = []

    for current_dir in execution_dirs:
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



def execute_global_application(application: str, arguments_and_placeholders: dict[str, list[Node]],placeholder_functions: dict[str, MateModule], config_values: dict[str, Any], execution_dirs: list[Path]) -> int:
    ret_process_report = []

    for dir in execution_dirs:
        subst_args = resolve_cli_args(arguments_and_placeholders, placeholder_functions, dir)
        execution_status = run_application(application, subst_args, execution_dir=dir, check=False)
        ret_process_report.append((str(dir), execution_status))

    return ret_process_report