from colorama import Fore, Back, Style, init

init(autoreset=True)  # Automatically reset after each print

def message(message: str):
    print(Fore.WHITE + message)


def info(message: str):
    print(Fore.GREEN + "[INFO] " + Fore.WHITE + message)


def warning(message: str):
    print(Fore.YELLOW + "[WARNING] " + Fore.WHITE + message)


def error(message: str):
    print(Fore.RED + "[ERROR] " + Fore.WHITE + message)

