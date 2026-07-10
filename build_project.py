import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

PACKAGE_NAME = "mate"
COMMAND_NAME = "mate"

PROJECT_ROOT = Path(__file__).parent.resolve()
PYINSTALLER_ENTRY_POINT = PROJECT_ROOT / "build_entry.py"

DIST_DIRECTORY = PROJECT_ROOT / "dist"
WHEEL_DIRECTORY = DIST_DIRECTORY / "wheel"
EXECUTABLE_DIRECTORY = DIST_DIRECTORY / "executable"
PYINSTALLER_WORK_DIRECTORY = PROJECT_ROOT / "build" / "pyinstaller"
PYINSTALLER_SPEC_DIRECTORY = PROJECT_ROOT / "build" / "pyinstaller-spec"


def run_command(
    command: List[str],
    cwd: Path,
    check: bool = True,
) -> int:
    """Run a command in a subprocess and stream its combined output."""

    print(f"\n[{cwd.name}]> {' '.join(command)}")

    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if process.stdout is not None:
            for line in process.stdout:
                print(line, end="")

        return_code = process.wait()

        if check and return_code != 0:
            raise subprocess.CalledProcessError(return_code, command)

        return return_code

    except FileNotFoundError:
        print(
            f"Error: command '{command[0]}' was not found.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    except subprocess.CalledProcessError as error:
        print(
            f"\nCommand failed with exit code {error.returncode}.",
            file=sys.stderr,
        )
        raise SystemExit(error.returncode)


def module_is_available(module_name: str) -> bool:
    """Return True when a Python module can be imported."""

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import importlib.util, sys; "
                f"sys.exit(0 if importlib.util.find_spec('{module_name}') else 1)"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    return result.returncode == 0


def require_build_dependencies() -> None:
    """Verify that the wheel and executable build tools are installed."""

    missing_packages = []

    if not module_is_available("build"):
        missing_packages.append("build")

    if not module_is_available("PyInstaller"):
        missing_packages.append("pyinstaller")

    if not missing_packages:
        return

    packages = " ".join(missing_packages)

    print(
        "\nMissing build dependencies.\n"
        "Install them in the active virtual environment with:\n\n"
        f"    {sys.executable} -m pip install {packages}\n",
        file=sys.stderr,
    )

    raise SystemExit(1)


def uninstall_package() -> None:
    """Uninstall the currently installed package."""

    print(f"\n--- Uninstalling previous version of '{PACKAGE_NAME}' ---")

    run_command(
        [
            sys.executable,
            "-m",
            "pip",
            "uninstall",
            "-y",
            PACKAGE_NAME,
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )


def install_package(editable: bool, clean: bool) -> None:
    """Install the project into the active Python environment."""

    if clean:
        uninstall_package()

    install_command = [
        sys.executable,
        "-m",
        "pip",
        "install",
    ]

    if editable:
        print(
            f"\n--- Installing '{PACKAGE_NAME}' in editable mode ---"
        )
        install_command.append("-e")
    else:
        print(f"\n--- Installing '{PACKAGE_NAME}' ---")

    install_command.append(".")

    run_command(
        install_command,
        cwd=PROJECT_ROOT,
    )

    print(
        f"\nSuccessfully installed '{PACKAGE_NAME}'. "
        f"You can now use the '{COMMAND_NAME}' command."
    )


def clean_build_directories() -> None:
    """Remove artifacts produced by previous builds."""

    directories = [
        WHEEL_DIRECTORY,
        EXECUTABLE_DIRECTORY,
        PYINSTALLER_WORK_DIRECTORY,
        PYINSTALLER_SPEC_DIRECTORY,
    ]

    for directory in directories:
        if directory.exists():
            print(f"Removing {directory}")
            shutil.rmtree(directory)


def build_wheel() -> None:
    """Build the project's wheel distribution."""

    print(f"\n--- Building wheel for '{PACKAGE_NAME}' ---")

    WHEEL_DIRECTORY.mkdir(parents=True, exist_ok=True)

    run_command(
        [
            sys.executable,
            "-m",
            "build",
            "--wheel",
            "--outdir",
            str(WHEEL_DIRECTORY),
        ],
        cwd=PROJECT_ROOT,
    )


def build_executable() -> None:
    """Build a standalone executable with PyInstaller."""

    print(f"\n--- Building standalone executable for '{PACKAGE_NAME}' ---")

    if not PYINSTALLER_ENTRY_POINT.is_file():
        print(
            f"Error: PyInstaller entry point does not exist:\n"
            f"    {PYINSTALLER_ENTRY_POINT}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    EXECUTABLE_DIRECTORY.mkdir(parents=True, exist_ok=True)
    PYINSTALLER_WORK_DIRECTORY.mkdir(parents=True, exist_ok=True)
    PYINSTALLER_SPEC_DIRECTORY.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        COMMAND_NAME,
        "--paths",
        str(PROJECT_ROOT / "src"),
        "--distpath",
        str(EXECUTABLE_DIRECTORY),
        "--workpath",
        str(PYINSTALLER_WORK_DIRECTORY),
        "--specpath",
        str(PYINSTALLER_SPEC_DIRECTORY),
        str(PYINSTALLER_ENTRY_POINT),
    ]

    run_command(
        command,
        cwd=PROJECT_ROOT,
    )


def build_distributions(clean: bool) -> None:
    """Build the wheel and standalone executable."""

    require_build_dependencies()

    if clean:
        clean_build_directories()

    build_wheel()
    build_executable()

    executable_suffix = ".exe" if sys.platform == "win32" else ""
    executable_path = (
        EXECUTABLE_DIRECTORY / f"{COMMAND_NAME}{executable_suffix}"
    )

    wheels = sorted(WHEEL_DIRECTORY.glob("*.whl"))

    print("\n--- Build completed successfully ---")

    if wheels:
        print(f"Wheel:      {wheels[-1]}")

    print(f"Executable: {executable_path}")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install or build the mate CLI tool."
    )

    parser.add_argument(
        "-e",
        "--editable",
        action="store_true",
        help="Install the project in editable mode.",
    )

    parser.add_argument(
        "--build",
        action="store_true",
        help="Build a wheel and standalone executable.",
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help=(
            "For installation, uninstall the existing package first. "
            "For builds, remove previous build artifacts first."
        ),
    )

    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    if args.editable and args.build:
        print(
            "Error: --editable and --build cannot be used together.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    if args.build:
        build_distributions(clean=args.clean)
    else:
        install_package(
            editable=args.editable,
            clean=args.clean,
        )


if __name__ == "__main__":
    main()