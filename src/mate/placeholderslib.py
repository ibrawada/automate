
from mate import utilities

import importlib
from pathlib import Path

def extract_placeholders(input: str) -> tuple[list[str], list[str]]:
    config_placeholders = []
    function_placeholders = []
    
    start = -1
    placeholder = ""
    for i in range(0, len(input)):
        if input[i] == '%':
            # Start of placeholder found
            if start == -1:
                start = i
            # End of placeholder found
            else:
                placeholder = input[start+1:i]
                start = -1
        
                # Analyse if the placeholder is a config value or a function
                if '[' in placeholder and ']' in placeholder:
                    function_placeholders.append(placeholder)
                else:
                    config_placeholders.append(placeholder)

        # Detect error case -> if start has a value other than default and the end of arg parameter was reached 
        # this means that there was no end % 
    if start != -1:
        print(f"[ERROR] argument {input} has no ending % delimiter")
        # TODO throw an exception and break execution

    return (config_placeholders, function_placeholders)



def substitute_config_placeholders(input: str, placeholders: list[str], config_values: dict) -> list[str]:
    substituted_tokens = input

    for placehoder in placeholders:
        section, entry = placehoder.split(':')
        substituted_tokens = substituted_tokens.replace(f"%{placehoder}%", config_values[section][entry])

    return substituted_tokens



def substitute_function_placeholders(input: str, placeholders: list[str], working_dir: Path) -> list[str]:
    # Check whether this creates a copy or NOT
    substituted_tokens = input

    for placeholder in placeholders:
        function_module = importlib.import_module(f".functions.{placeholder.removesuffix('[]')}", package="mate")
        placeholder_value = function_module.run(working_dir)
        substituted_tokens = substituted_tokens.replace(f"%{placeholder}%", placeholder_value)

    return substituted_tokens

def extract_argument_placeholders(arguments: list[str]) -> dict:
    argument_placeholders = {}
    for arg in arguments:
        config_placeholders, function_placeholders = extract_placeholders(arg)
        argument_placeholders[arg]= {
                "config" : config_placeholders,
                "function" : function_placeholders
            }
        
    return argument_placeholders



def substitute_arguments_function_placeholders(args: list[str], arg_placeholders: dict, working_dir: Path) -> list[str]:
    ret_substituted_arguments = []
        
    for argument, placeholders in arg_placeholders.items():
        function_placeholders = placeholders["function"]
        substituted_argument = substitute_function_placeholders(argument, function_placeholders, working_dir)
        ret_substituted_arguments.append(substituted_argument)

    return ret_substituted_arguments    



def substitute_argument_placeholders_from_configs(args: list[str], argument_placeholders: dict, configs: dict[str, dict[str, str]]) -> list[str]:
    ret_substituted_arguments = []
        
    for argument, placeholders in argument_placeholders.items():
        config_placeholders = placeholders["config"]
        substituted_argument = substitute_config_placeholders(argument, config_placeholders, configs)
        ret_substituted_arguments.append(substituted_argument)

    return ret_substituted_arguments

