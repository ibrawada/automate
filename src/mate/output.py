from colorama import Fore, Back, Style, init

from mate import globals
from mate.executors import ExecutionResult

init(autoreset=True)  # Automatically reset after each print



def message(message: str):
    print(Fore.WHITE + message)



def info(message: str):
    print(Fore.GREEN + "[INFO] " + Fore.WHITE + message)



def warning(message: str):
    print(Fore.YELLOW + "[WARNING] " + Fore.WHITE + message)



def error(message: str):
    print(Fore.RED + "[ERROR] " + Fore.WHITE + message)



# Command output is indented so it can be told apart from the folder lines
def _print_details(details: str):
    for line in details.splitlines():
        print(f"    {line}")



def status_report(report: list[ExecutionResult]):
    print(Fore.BLUE + "[REPORT]")
    for result in report:
        if result.returncode == globals.SUCCESS_CODE:
            print(Fore.GREEN + f"{result.cwd}")
        elif result.returncode == globals.WARNING_CODE:
            print(Fore.YELLOW + f"{result.cwd}({result.returncode})")
            _print_details(result.stdout)
        else:
            print(Fore.RED + f"{result.cwd}({result.returncode})")
            _print_details(result.stderr)



def suggest_retry(report: list[ExecutionResult]):
    message = "--only="
    retry_folders = []
    for result in report:
        if result.returncode != globals.SUCCESS_CODE:
            retry_folders.append(str(result.cwd))

    if len(retry_folders) != 0:
        message += ','.join(retry_folders)
        info(f"To retry with failed folders use: {message}")