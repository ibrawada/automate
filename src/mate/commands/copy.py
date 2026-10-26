# ops/copy.py
import argparse
import shutil
import sys
from pathlib import Path

from mate import globals
from mate.executors import ExecutionResult, ExecutorType


def build_parser(p: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Builds the argument parser for the copy command.
    """
    p.add_argument("-i", "--input", required=True,
                   help="Source file or folder to copy.")
    p.add_argument("-d", "--destination", default=".", required=False,
                   help="Destination folder or full file path.")
    return p



def get_default_config() -> dict[str, dict[str, str]]:
    return {
        "copy":
        {

        }
    }



def result(cwd, returncode: int, stdout: str = "", stderr: str = "") -> ExecutionResult:
    return ExecutionResult(command_name="copy", command_args=[], cwd=Path(cwd), executor=ExecutorType.EMBEDDED,
                           returncode=returncode, stdout=stdout, stderr=stderr)



def main(cwd, args, env: dict) -> ExecutionResult:
    """
    Executes the copy operation based on parsed arguments.
    This function is called for each project folder `mate` operates on.
    """
    source_path = Path(args.input)
    dest_path = Path(cwd) / args.destination

    if not source_path.exists():
        return result(cwd, globals.ERROR_CODE, stderr=f"Source path does not exist: {source_path}")

    try:
        if source_path.is_dir():
            # Copy directory. shutil.copytree copies the source *into* the destination.
            # If dest_path is 'path/to/new_name', the contents of source_path
            # will be placed in 'path/to/new_name'.
            shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
            return result(cwd, globals.SUCCESS_CODE, stdout=f"Copied directory '{source_path}' to '{dest_path}'")

        else: # Source is a file
            # If destination is an existing directory, copy the file into it.
            # Otherwise, copy the file to the specified path (potentially renaming it).
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, dest_path)
            return result(cwd, globals.SUCCESS_CODE, stdout=f"Copied file '{source_path}' to '{dest_path}'")

    except Exception as e:
        return result(cwd, globals.ERROR_CODE, stderr=f"Exception during copy operation: {e}")



if __name__ == "__main__":
    wsd_parser = argparse.ArgumentParser(add_help=False)
    wsd_parser.add_argument("--wsd", type=Path, default=".")
    wsd_args, rest_args = wsd_parser.parse_known_args(sys.argv[1:])
    

    parser = build_parser(
        argparse.ArgumentParser(prog=f"Nothing to say")
    )

    parsed_args = parser.parse_args(args=rest_args)


    main(wsd_args.wsd, parsed_args, {})