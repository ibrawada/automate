
import sys
import argparse


setting = "SECT:Opt=V"
# try:
#     section_option, value = setting.split('=', 1)
# except ValueError:
#     print(f"Error: Invalid setting format '{setting}'. Use 'section:key=value'.")
#     section, option = section_option.split(':', 1)
    

def split_setting(setting: str) -> tuple[str, str, str]:
    section = ""
    option = ""
    value = ""

    if ":" in setting:
        section, option_value = setting.split(':', 1)
        
        if "=" in option_value:
            option, value = option_value.split('=', 1)
        else:
            # Only option provided
            option = option_value

    # only section provided nothing else
    else:
        section = setting

    return (section, option, value)


section, option, value = split_setting(setting)
print(f"section:{section} option:{option} value:{value}")

# def cli(args = None):
#     # --- Initial Setup: Parse only --cwd to set the context ---
#     # This is only required if the cwd is not the call directory
#     # cwd_parser = argparse.ArgumentParser(add_help=False)
#     # cwd_parser.add_argument("--cwd", type=Path, default=".")
#     # cwd_args, _ = cwd_parser.parse_known_args(argv)
#     # set_cwd(cwd_args.cwd)
#     print(sys.argv)

#     for arg in sys.argv:
#         if '%' in arg:
#             # Count number of % chars in the arg. The number may not be odd
#             print(arg.count('%'))
#             arg.partition()


# if __name__ == "__main__":
#     sys.exit(cli())