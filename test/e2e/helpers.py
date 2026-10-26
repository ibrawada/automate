import re
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")
REPORT_ENTRY = re.compile(r"^(?P<dir>.*?)(?:\((?P<status>-?\d+)\))?$")


@dataclass
class Result:
    code: int | None
    out: str
    err: str
    # Folder name -> exit status, parsed from the "[REPORT]" line (empty if no report was printed)
    report: dict[str, int] = field(default_factory=dict)


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE.sub("", text)


def parse_report(out: str) -> dict[str, int]:
    """Parses the block printed by output.status_report:

    [REPORT]
    <dir>
    <dir>(<status>)
        <indented command output>
    """
    report = {}
    in_report = False
    for line in strip_ansi(out).splitlines():
        if line.startswith("[REPORT]"):
            in_report = True
            continue
        if not in_report:
            continue
        if line.startswith("["):
            in_report = False
            continue
        if not line.strip() or line.startswith(" "):
            continue
        match = REPORT_ENTRY.match(line.strip())
        status = int(match["status"]) if match["status"] else 0
        report[Path(match["dir"]).name] = status
    return report


def read_toml(path: Path) -> dict:
    with open(path, "rb") as file:
        return tomllib.load(file)


def git(cwd: Path, *args: str, check: bool = True) -> str:
    completed = subprocess.run(["git", *args], cwd=cwd, check=check, capture_output=True, text=True)
    return completed.stdout.strip()
