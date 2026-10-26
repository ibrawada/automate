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



def status_report(report: list[ExecutionResult]):
    print(Fore.BLUE + "[REPORT]")
    for result in report:
        if result.returncode == globals.SUCCESS_CODE:        
            print(Fore.GREEN + f"{result.cwd}")# dir 
        elif result.returncode == globals.WARNING_CODE:
            print(Fore.YELLOW + f"{result.cwd}")
            print(f"{result.stdout}")
        else:
            print(Fore.RED + f"{result.cwd}")
            print(f"{result.stderr}")



def suggest_retry(report: list[ExecutionResult]):
    message = "--only="
    retry_folders = []
    for result in report:
        if result.returncode != globals.SUCCESS_CODE:
            retry_folders.append(dir)

    if len(retry_folders) != 0:
        message += ','.join(retry_folders)
        info(f"To retry with failed folders use: {message}")