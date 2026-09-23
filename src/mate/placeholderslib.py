import importlib

from typing import Any

from pathlib import Path

from dataclasses import dataclass, field
from enum import Enum, auto

from mate import output
from mate import globals


class NodeType(Enum):
    FUNCTION = auto()
    STRING = auto()
    # NUMBER = auto()
    CONFIG = auto()


@dataclass
class Node:
    id: int
    value = ""
    parent: Node | None
    children: list[Node] = field(default_factory=list)
    level: int = 0
    position: int = 0
    type: NodeType = NodeType.STRING

# a placeholder is defined inside a resolution slot which is delimited by 2 %% chars


# Following possible placeholders combinations
# - %<placeholder>%
# - %<placeholder>abc%
# - abc%<placeholder>%
# - abc%<placeholder>%abc
  

# The placeholder itself can be either
# - config placeholder: %vars:name%
#   - The value of the vars:name is extracted from local or global config value
#   - The value is extracted only once
# - function placeholder: %folder_name[]%
#   - The value is extracted for each processed directory

# (!) Not possible is having 2 placeholders in sequence inside one resolution slot

# # Future work
# function placeholders can have nested arguments
# %function[vars:option]%
# %function[vars:option1, vars:option2]%
# %function["string"]$
# %function["string", vars:option3]%
# The nesting can go even deeper
# %func1[func2[]]%
# %func1[func2["arg", fun3[vars:option, "arg2"]]] and so on
# - execution sequence shall be from bottom to top, left to right

def find_pc_delimiters(input: str) -> tuple[int, int] | None:
    # Find placeholder delimiters
    pc_start = None
    pc_end = None 
    for i in range(0, len(input)):
            current_char = input[i]
            if current_char == '%':
                if pc_start == None:
                    pc_start = i
                else:
                    pc_end = i

    # No delimiters found -> no placeholders present
    if pc_start == None:
        return None, None
    
    # Error if wrong number of delimiters was found
    if pc_start != None and pc_end == None:
        output.error(f"Found only one placeholder delimiter in {input} at {pc_start}")

    return pc_start+1, pc_end



# This will create at least one Node tree
def create_pc_tree(input: str,index: int = 0, parent: Node | None = None, tree: list | None = None) -> tuple[list, int]:
    # if input == "":
    #     return tree
    
    # Todo: Remove this unnecessary member later
    current_position = 0

    if parent == None:
        current_id = 0
        current_level = 0
        current_node = Node(0,parent=None)
    else:
        current_id = parent.id+1
        current_level = parent.level + 1
        current_node = Node(current_id, parent, [], current_level, current_position)
        parent.children.append(current_node)

    # if tree == None:
    #     tree = {}
    tree.append(current_node)
    # This can only be done recursively.
    while index < len(input):
        current_char = input[index]
        # print(f"index:{index}, current_char:{current_char}")


        if current_char == '[':# -> start new level and
            current_node.type = NodeType.FUNCTION
            tree, index = create_pc_tree(input,index+1,current_node, tree)
            current_id = tree[len(tree)-1].id

        elif current_char == ']': # -> End of the level
            # Check first if the created Node is empty -> then delete
            if len(current_node.value) == 0:
                tree.pop() # Remove last added node when its empty
            return tree, index

        elif current_char == ',': # -> create new node on the same level but incremented position
            if parent == None or parent.type != NodeType.FUNCTION:
                output.error(f"Cannot have placeholders with , without a parent of type function")
                globals.exit_mate(globals.ERROR_CODE)
            current_id += 1
            current_position += 1
            current_node = Node(current_id, parent, [], current_level, current_position)
            tree.append(current_node)
            parent.children.append(current_node)

        else: # Fill the value of the Node
            current_node.value += current_char
            if current_char == ':':
                current_node.type = NodeType.CONFIG

        index += 1
    # Todo: Add counters to [ and ] for error detection
    return tree, index

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



def substitute_placeholders(arg_placeholders: dict, configs: dict[str, dict[str, Any]], working_dir: Path) -> list[str]:
    ret_substituted_arguments = []
        
    for argument, placeholders in arg_placeholders.items():
        function_placeholders = placeholders["function"]
        config_placeholders = placeholders["config"]
        substituted_argument = substitute_config_placeholders(argument, config_placeholders, configs)
        substituted_argument = substitute_function_placeholders(substituted_argument, function_placeholders, working_dir)
        ret_substituted_arguments.append(substituted_argument)

    return ret_substituted_arguments      



def extract_argument_placeholders(arguments: list[str]) -> dict:
    argument_placeholders = {}
    for arg in arguments:
        config_placeholders, function_placeholders = extract_placeholders(arg)
        argument_placeholders[arg]= {
                "config" : config_placeholders,
                "function" : function_placeholders
            }
        
    return argument_placeholders




# def substitute_arguments_function_placeholders(args: list[str], arg_placeholders: dict, working_dir: Path) -> list[str]:
#     ret_substituted_arguments = []
        
#     for argument, placeholders in arg_placeholders.items():
#         function_placeholders = placeholders["function"]
#         substituted_argument = substitute_function_placeholders(argument, function_placeholders, working_dir)
#         ret_substituted_arguments.append(substituted_argument)

#     return ret_substituted_arguments    



# def substitute_argument_placeholders_from_configs(args: list[str], argument_placeholders: dict, configs: dict[str, dict[str, Any]]) -> list[str]:
#     ret_substituted_arguments = []
        
#     for argument, placeholders in argument_placeholders.items():
#         config_placeholders = placeholders["config"]
#         substituted_argument = substitute_config_placeholders(argument, config_placeholders, configs)
#         ret_substituted_arguments.append(substituted_argument)

#     return ret_substituted_arguments

