from __future__ import annotations
import argparse
import os
import ast
from pathlib import Path
from configparser import ConfigParser
from enum import Enum
from typing import Any


APP_NAME = "mate"
GLOBAL_CONFIG_FILE = "global.ini"
LOCAL_CONFIG_FILE = "local.ini"
CWD = Path(".")

# ---- paths ---------------------------------------------------------------
def set_cwd(path: Path):
    global CWD
    CWD = path

def get_cwd() -> Path:
    return CWD

def get_home_dir() -> Path:
    # Prefer Windows' %USERPROFILE% when available; fall back to Path.home()
    return Path(os.environ.get("USERPROFILE") or Path.home())

def get_config_dir() -> Path:
    return get_home_dir() / f".{APP_NAME}"

def get_global_config_path() -> Path:
    return get_config_dir() / GLOBAL_CONFIG_FILE

def get_local_config_path() -> Path:
    return CWD / Path(f".{APP_NAME}") / LOCAL_CONFIG_FILE


# ---- config I/O ----------------------------------------------------------

DEFAULT_LOCAL_CONFIG = {
    "folders": {
        "exclude":"['build']"
    }
}


DEFAULT_GLOBAL_CONFIG = {
    "folders": {
        "exclude":"['.mate', '.git']"
    }
}

def ensure_config_exists(path, config) -> None:
    """Create ~/.toolname/config.ini with defaults if it doesn't exist."""
    cfg_path = path
    cfg_dir = cfg_path.parent
    cfg_dir.mkdir(parents=True, exist_ok=True)

    if not cfg_path.exists():
        cfg = ConfigParser()
        for section, values in config.items():
            cfg[section] = values
        _atomic_write_config(cfg, cfg_path)

def _atomic_write_config(cfg: dict, path: Path) -> None:
    """Write config atomically to avoid partial files."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        cfg.write(f)
    tmp_path.replace(path)  # atomic on same filesystem

def load_config(path) -> ConfigParser:
    """Load config, creating defaults if missing."""
    cfg = ConfigParser()
    
    cfg.read(path, encoding="utf-8")
    return cfg

def apply_overrides(cfg: ConfigParser, kv_pairs: list[str]) -> bool:
    """
    Apply key=value overrides. Keys can be 'section.key' or just 'key'
    (which goes to [general]). Returns True if anything changed.
    """
    changed = False
    for pair in kv_pairs:
        if "=" not in pair:
            raise ValueError(f"Invalid override '{pair}'. Use key=value.")
        key, value = pair.split("=", 1)
        if "." in key:
            section, option = key.split(".", 1)
        else:
            section, option = "general", key
        if not cfg.has_section(section):
            cfg.add_section(section)
        if cfg.get(section, option, fallback=None) != value:
            cfg.set(section, option, value)
            changed = True
    return changed



class Action(Enum):
    APPEND = "append"
    REMOVE = "remove"
    

def update_config(config_path: Path, settings: list[str], args: argparse.Namespace):
    """Updates a configuration file with new settings."""
    parser = ConfigParser()
    parser.read(config_path)

    action = None
    if not args.append and not args.remove:
        action = Action.APPEND
    elif args.append:
        action = Action.APPEND
    elif args.remove:
        action = Action.REMOVE

    for setting in settings:
        try:
            key_part, new_value_str = setting.split('=', 1)
            section, key = key_part.split(':', 1)
        except ValueError:
            print(f"Error: Invalid setting format '{setting}'. Use 'section:key=value'.")
            continue

        if not parser.has_section(section):
            parser.add_section(section)


        # Get the existing list from the config
        if parser.has_option(section, key):
            existing_value_str = parser.get(section, key)            
            try:
                existing_list = ast.literal_eval(existing_value_str)
                if isinstance(existing_list, list):                    
                    # Modify the list
                    if action == Action.APPEND:
                        existing_list.append(new_value_str)
                    elif action == Action.REMOVE:
                        if new_value_str in existing_list:
                            existing_list.remove(new_value_str)
                    
                    parser.set(section, key, str(existing_list))
                    print(f"Updated [{section}] {key} = {existing_list}")
                else:
                    parser.set(section, key, new_value_str)
                    print(f"Set [{section}] {key} = {new_value_str}")
            except: # If not a list then overwrite the value
                parser.set(section, key, new_value_str)
                print(f"Set [{section}] {key} = {new_value_str}")
        else: # Set / create the entry
            parser.set(section, key, new_value_str)
            print(f"Set [{section}] {key} = {new_value_str}")


    _atomic_write_config(parser, config_path)

# ---- CLI -----------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog=APP_NAME,
        description=f"{APP_NAME}: example tool that uses a per-user config file",
    )
    p.add_argument(
        "--global", "-g",
        dest="global_config",
        action="store_true",
        help="Target the global configuration."
    )
    p.add_argument(
        "--append", "-a",
        action="store_true",
        help="Append a value to a list in the config (not yet implemented)."
    )
    p.add_argument(
        "--remove", "-r",
        action="store_true",
        help="Remove a value from a list in the config (not yet implemented)."
    )
    p.add_argument(
        "--show", 
        action="store_true",
        help="Remove a value from a list in the config (not yet implemented)."
    )
    p.add_argument(
        "settings",
        nargs="*",
        help="Settings to update, in 'section:key=value' format."
    )

    return p

# mate config --global|--local(default) exec.notepad="path/to/notepad"
# mate config --local var.pre-commit="path/to/pre-commit.yml" 

def _merge_configs(target_dict: dict, source_config: ConfigParser):
    """
    Merges settings from a ConfigParser object into a dictionary.
    It handles string representations of lists by parsing and merging them.
    """
    for section in source_config.sections():
        if section not in target_dict:
            target_dict[section] = {}
        for key, value_str in source_config.items(section):
            try:
                # Safely evaluate string to a Python literal (e.g., "['a', 'b']" -> ['a', 'b'])
                value = ast.literal_eval(value_str)
            except (ValueError, SyntaxError):
                # Not a literal, treat as a plain string
                value = value_str

            if isinstance(value, list):# and key in target_dict[section] and isinstance(target_dict[section][key], list):
                if key in target_dict[section]:
                    target_dict[section][key].extend(value)
                else:
                    target_dict[section][key] = value
            else:
                target_dict[section][key] = value

def config_update(argv: list[str] | None = None):
    args = build_parser().parse_args(argv)

    if args.show:
        configs = config_read()
        print("--- Configuration ---")
        print(f"-local config: {get_local_config_path()}")
        print(f"-global config: {get_global_config_path()}")
        for section, map in configs.items():
            for k, v in map.items():
                print(f"{section}.{k} = {v}")
        return 0

    if args.settings:
        if args.global_config:
            config_path = get_global_config_path()
            ensure_config_exists(config_path, DEFAULT_GLOBAL_CONFIG)
        else:
            config_path = get_local_config_path()
            ensure_config_exists(config_path, DEFAULT_LOCAL_CONFIG)
        
        update_config(config_path, args.settings, args)
        print(f"\nConfiguration updated in: {config_path}")
        return 0

def config_read() -> dict[str, dict[str, Any]]:
    # Load config every time the tool runs
    global_path = get_global_config_path()
    
    ensure_config_exists(global_path, DEFAULT_GLOBAL_CONFIG)
    cfg_global = load_config(global_path)

    combined_configs_dict = {}
    _merge_configs(combined_configs_dict, cfg_global)

    if os.path.exists(get_local_config_path()):
        local_path = get_local_config_path()
        cfg_local = load_config(local_path)
        _merge_configs(combined_configs_dict, cfg_local)

    return combined_configs_dict

if __name__ == "__main__":
    raise SystemExit(config_main())
