from pathlib import Path

def run(cwd: Path, args: list[str]) -> list[str]:    
    ret_vals = []
    for arg in args:
        ret_vals.append(arg.upper())
    return ret_vals
