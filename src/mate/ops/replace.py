
# ops/replace.py
import argparse
from pathlib import Path
import sys

def build_parser(p: argparse.ArgumentParser) -> argparse.ArgumentParser:
    p.add_argument("--cwd", type=Path, default=Path.cwd(),
                   help="Base dir for relative paths")
    p.add_argument("-f", "--file", required=True, help="Path to file")
    p.add_argument("-i", "--input", required=False, help="String to replace")
    p.add_argument("-o", "--output", required=False, help="Replacement string")
    p.add_argument("-l", "--line", required=False, help="Line to be extended")
    p.add_argument("-nl", "--new-line", required=False, help="Line to extend")
    p.add_argument("-a", "--append", action="store_true", help="Append to line")
    p.add_argument("-p", "--prepend", action="store_true", help="String to prepend to line")
    return p


def main(cwd, args, env: dict) -> int:
    path = Path(cwd) / Path(args.file)
    old_text = path.read_text(encoding="utf-8")

    # print("Replace.py")
    if args.input and args.output:
        new_text = old_text.replace(args.input, args.output)
    else:
        # find the line that matches the args.line (where args.line can be an incomplete line example name=* which should match to name="somename")
        lines = old_text.splitlines()
        new_line = args.new_line
        input_text_line = ""
        text_line_found = False
        for _, text_line in enumerate(lines):
            # print(f'text_line: {text_line}')
            if args.line in text_line:
                input_text_line = text_line
                text_line_found = True
                if args.append:
                    new_line = text_line +'\n' + new_line 
                elif args.prepend:
                    new_line = new_line + '\n' + text_line
                break
        if text_line_found:
            # print(f'input_text_line: {input_text_line} to be replace by {new_line}')
            new_text = old_text.replace(input_text_line, new_line)

    # new_text = old_text.replace(args.input, args.output)
    path.write_text(new_text, encoding="utf-8")    
    return 0


if __name__ == "__main__":
    parser = build_parser(
    # argparse.ArgumentParser(prog=f"{root_parser.prog} {root_args.command}")
    argparse.ArgumentParser(prog=f"Nothing to say")
    )
    parsed_args = parser.parse_args(args=sys.argv[1:])


    main(parsed_args.cwd, parsed_args, {})