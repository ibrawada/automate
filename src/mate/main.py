#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
import importlib
# For the executable
# from .config import config_read, config_update, set_cwd

# For debugging
from config import config_read, config_update, set_cwd



def run(cmd: list[str], cwd: str | None = None, check: bool = True) -> int:
    dirname = Path(cwd).name
    print(f"({dirname}/) :> '{' '.join(cmd)}")

    try:
        completed = subprocess.run(cmd, cwd=cwd, check=check)
        return completed.returncode
    except FileNotFoundError as e:
        print(f"[mate] ERROR: command not found: {cmd[0]}\n{e}", file=sys.stderr)
        return 127
    except subprocess.CalledProcessError as e:
        return e.returncode



def collect_script_tasks() -> list[str]:
    ops_directory = Path(__file__).parent / "ops"
    names = sorted(
        p.stem for p in ops_directory.glob("*.py") if p.stem != "__init__"
    )
    return names


def direct_call(op_folders: list[str], args: list[str], folders_vars: dict) -> int:
    for folder in op_folders:
        args = substitute_local_variables(args, folders_vars[folder])
        run(args, cwd=folder, check=False)
        # run(args, cwd=folder)


def load_command(operation):
    """Import ops.<cmd> and return the module."""
    return importlib.import_module(f".ops.{operation}", package="mate")



def forward_to_locals(folders: list[str], operation, args, environment: dict, folders_vars: dict) -> int:
    # Run the module's entry (prefer .main, fallback to .run)

    if not hasattr(operation, "main"):
        print(f"Error no main entry point for {operation}")
        sys.exit(1)

    for folder in folders:
        # per = _with(args, cwd=Path(folder))
        subst_args = substitute_local_variables(args, folders_vars[folder])
        parser = operation.build_parser(
            # argparse.ArgumentParser(prog=f"{root_parser.prog} {root_args.command}")
            argparse.ArgumentParser(prog=f"Nothing to say")
        )
        parsed_args = parser.parse_args(subst_args)
        # print(f"executing copy: {subst_args}")
        operation.main(folder, parsed_args, environment)

def forward_to_config_exes(folders: list[str], exe: str, args: list[str], folders_vars: dict) -> int:
    for folder in folders:        
        args = substitute_local_variables(args, folders_vars[folder])
        run([exe, *args], cwd=folder)



def collect_folders(cwd: Path, ignore_folders: list[str]) -> list[str]:
    # iterate over cwd and collect only the direct folder in level 1

    folders = []
    for item in cwd.iterdir():
        op_folder = str(item)
        if any(f in op_folder for f in ignore_folders):
            continue
        if item.is_dir():
            folders.append(str(item))
    return folders


def make_root_parser(commands):
    p = argparse.ArgumentParser(
        prog=f"python {Path(sys.argv[0]).name}",
        description="Ops command runner",
        add_help=False,
    )
    
    p.add_argument("command", nargs="?", help=f"One of: {', '.join(sorted(commands))}")
    # p.add_argument("--cwd", type=Path, default=Path.cwd(),
    #                help="Directory containing projects to operate on.")
    p.add_argument("--cwd", type=Path, default=".",
    # p.add_argument("--cwd", type=Path, default='E:/Gitea/_test_ProductsPipeline',
                   help="Directory containing projects to operate on.\nDefault is the current open directory")
    p.add_argument("-h", "--help", action="store_true", help="Show this help")

    
    return p


def substitute_config_variables(args: list[str], configs: dict) -> list[str]:
    """
    Iterates through a list of arguments and replaces any variables
    in the format @<section>.<key> with values from the configuration.
    """
    substituted_args = []
    for arg in args:
        if arg.startswith('%') and ':' in arg:
            variable_name = arg[1:]
            section, key = variable_name.split(':', 1)
            
            # Safely get the value from the nested config dictionary
            value = configs.get(section, {}).get(key)
            
            if value is not None:
                substituted_args.append(str(value))
                print(f"Substituted '{arg}' with '{value}'")
            else:
                substituted_args.append(arg) # Keep original if not found
                # Variable not found in config, exit with an error
                print(f"Error: Variable '{arg}' not found in configuration.", file=sys.stderr)
                sys.exit(1)
        else:
            substituted_args.append(arg)
    return substituted_args


def create_local_variables(cwd: Path) -> dict:
    return {
        "folder_name": cwd.name
    }

def substitute_local_variables(args, local_vars: dict) -> list[str]:
    substituted_args = []
    pattern = r"%(\w+)"  # matches %folder_name and captures "folder_name"
    def replace_placeholder(match):
        key = match.group(1)          # "folder_name"
        return local_vars.get(key, match[0])   # replace if found, otherwise keep original

    for arg in args:
        # Todo: startswith is wrong. because the variable could be part of a text example "something something %folder_name Seomthing"
        # I need a way to find %folder_name in the text, take it out and replace it with the correct value
        interpolated_arg = re.sub(pattern, replace_placeholder, arg)
        substituted_args.append(interpolated_arg)
    return substituted_args




def cli(argv=None):
    """Main command-line-interface entry point."""
    if argv is None:
        argv = sys.argv[1:]

    # --- Initial Setup: Parse only --cwd to set the context ---
    # This allows config_read() to find the correct local config file.
    cwd_parser = argparse.ArgumentParser(add_help=False)
    # cwd_parser.add_argument("--cwd", type=Path, default="E:/Gitea/_test_ProductsPipeline")
    cwd_parser.add_argument("--cwd", type=Path, default=".")
    cwd_args, _ = cwd_parser.parse_known_args(argv)
    set_cwd(cwd_args.cwd)


    if len(argv) >= 2 and argv[0] == "config":
        return config_update(sys.argv[2:])
        

    configs = config_read()
    environment= configs.get("env", {})

    # Perform substitution on the raw argv before parsing
    substituted_argv = substitute_config_variables(argv, configs)

    script_tasks = collect_script_tasks()
    root_parser = make_root_parser(script_tasks)
    root_args, rest_args = root_parser.parse_known_args(substituted_argv)
    
    if root_args.help and not root_args.command:
        root_parser.print_help()
        return 0
    
    if not root_args.command:
        root_parser.error("a command is required.")
        return 1

    folders = []
    if configs["folders"].get("selection", ''):
        entry = configs["folders"]["selection"]
        selection = configs["folders"][entry]
        print(f"selection: {selection}")
        for folder in selection:
            folders.append(str(Path(root_args.cwd, folder)))
    else:
        folders = collect_folders(root_args.cwd, configs["folders"]["exclude"])
    
    print("folder: ", folders)
    return
    # Create variables that are local to a folder
    # ATM only folder_name is created
    folder_local_vars = {}
    for folder in folders:
        folder_local_vars[folder] = create_local_variables(Path(folder))
        

    if root_args.command in script_tasks:
        operation = load_command(root_args.command)
        return forward_to_locals(folders, operation, rest_args, environment, folder_local_vars)
    exe_path = configs.get("exe", {}).get(root_args.command)
    if exe_path:
        return forward_to_config_exes(folders, exe_path, rest_args, folder_local_vars)
    else:
        # Treat as an external command to run in each folder
        return direct_call(folders, substituted_argv, folder_local_vars)
        # return direct_call(folders, [root_args.command, *rest_args])


if __name__ == "__main__":
    # This block runs only when the script is executed directly (e.g., python src/mate/main.py)
    # It adds the 'src' directory to the path to allow the 'mate' package to be found.
    # This is not needed when the package is installed.
    SRC_DIR = Path(__file__).resolve().parent.parent
    if str(SRC_DIR) not in sys.path:
        sys.path.insert(0, str(SRC_DIR))
    sys.exit(cli())
