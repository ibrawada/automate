from colorama import Fore, Back, Style, init

from mate import globals

init(autoreset=True)  # Automatically reset after each print

def message(message: str):
    print(Fore.WHITE + message)


def info(message: str):
    print(Fore.GREEN + "[INFO] " + Fore.WHITE + message)


def warning(message: str):
    print(Fore.YELLOW + "[WARNING] " + Fore.WHITE + message)


def error(message: str):
    print(Fore.RED + "[ERROR] " + Fore.WHITE + message)


def status_report(report: list[str, int]):
    message = ""
    for dir, status in report:
        if status == globals.SUCCESS_CODE:        
            message += Fore.GREEN + dir 
        else:
            message += Fore.RED + dir + f"({status})"
        message += ", "

    print(Fore.BLUE + "[REPORT] " + Fore.WHITE + message)