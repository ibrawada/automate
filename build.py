import argparse
import subprocess
import sys
from pathlib import Path

# The name of the package as defined in pyproject.toml
PACKAGE_NAME = "mate"
PROJECT_ROOT = Path(__file__).parent.resolve()


def run_command(command: list[str], cwd: Path, check: bool = True):
    """Runs a command in a subprocess and streams its output."""
    print(f"[{cwd.name}]> {' '.join(command)}")
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8'
        )
        # Stream the output
        for line in iter(process.stdout.readline, ''):
            print(line, end='')
        
        process.wait()
        if check and process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)

    except FileNotFoundError:
        print(f"Error: Command '{command[0]}' not found. Is it in your PATH?", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\nCommand failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(e.returncode)

def main(args):
    """Uninstalls the old version, and builds and installs the new version."""
    print(f"--- Uninstalling previous version of '{PACKAGE_NAME}' ---")
    # The '-y' flag confirms the uninstall automatically.
    # We don't check for errors, as it's okay if the package wasn't installed.
    run_command([sys.executable, "-m", "pip", "uninstall", "-y", PACKAGE_NAME], cwd=PROJECT_ROOT, check=False)

    install_command = [sys.executable, "-m", "pip", "install"]
    if args.editable:
        print(f"\n--- Building and installing new version of '{PACKAGE_NAME}' in editable mode ---")
        install_command.append("-e")
    else:
        print(f"\n--- Building and installing new version of '{PACKAGE_NAME}' ---")
    
    install_command.append(".")
    run_command(install_command, cwd=PROJECT_ROOT)
    print(f"\n✅ Successfully installed '{PACKAGE_NAME}'. You can now use the 'automate' command.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build and install the automate tool.")
    parser.add_argument("-e", "--editable", action="store_true", help="Install in editable mode.")
    cli_args = parser.parse_args()
    main(cli_args)
