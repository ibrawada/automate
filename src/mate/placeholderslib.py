from __future__ import annotations
import importlib

from typing import Any

from pathlib import Path

from dataclasses import dataclass, field
from enum import Enum, auto

from mate import output
from mate import globals
from mate import config
from mate.utilities import MateModule


class NodeType(Enum):
    FUNCTION = auto()
    STRING = auto()
    CONFIG = auto()


@dataclass(kw_only=True)
class Node:
    id: int # Todo: Might irrelevant / Could be relevant in order to traverse the tree in ascending order
    parent: Node | None = None
    content: str = "" # Contains the pc string 
    value: Any | None = None # Contains the value of the pc after evaluation
    children: list[Node] = field(default_factory=list)
    resolved: bool = False
    depth: int = 0
    position: int = 0 # Todo: Might irrelevant
    type: NodeType = NodeType.STRING
    index: int | None = None

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


def extract_argument_placeholders(arguments: list[str]) -> dict[str, list[Node]]:
    argument_placeholders = {}
    for arg in arguments:
        start, end = find_pc_delimiters(arg)
        if start == None:
            argument_placeholders[arg] = None
            continue
        pc_tree = create_pc_tree(arg[start:end])
        argument_placeholders[arg] = pc_tree        
    return argument_placeholders



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



def create_pc_tree(input: str) -> list[Node]:    
    tree,_ = _create_pc_tree(input)
    # Finalize Tree initialization
    for index in range(0,len(tree)):
        tree[index].index = index
        if tree[index].type == NodeType.STRING:
            tree[index].resolved = True
            tree[index].value = tree[index].content
    return tree



# This will create at least one Node tree
def _create_pc_tree(input: str,index: int = 0, parent: Node | None = None, tree: list | None = None) -> tuple[list, int]:
    current_position = 0

    if parent == None:
        current_id = 0
        current_level = 0
        current_node = Node(id=0,parent=None)
    else:
        current_id = parent.id+1
        current_level = parent.depth + 1
        current_node = Node(id=current_id, parent=parent, depth=current_level, position=current_position)
        parent.children.append(current_node)

    if tree == None:
        tree = []
    tree.append(current_node)

    while index < len(input):
        current_char = input[index]

        if current_char == '[':# -> start new level and
            current_node.type = NodeType.FUNCTION
            tree, index = _create_pc_tree(input,index+1,current_node, tree)
            current_id = tree[len(tree)-1].id

        elif current_char == ']': # -> End of the level
            # Check: is the created Node is empty -> then delete this empty node
            if len(current_node.content) == 0:
                tree.pop() # Remove last added node when its empty
                parent.children.pop()
            return tree, index

        elif current_char == ',': # -> create new node on the same level but incremented position
            if parent == None or parent.type != NodeType.FUNCTION:
                output.error(f"Cannot have placeholders with , without a parent of type function")
                globals.exit_mate(globals.ERROR_CODE)
            current_id += 1
            current_position += 1
            current_node = Node(id=current_id, parent=parent, depth=current_level, position=current_position)
            tree.append(current_node)
            parent.children.append(current_node)

        else: # Fill the value of the Node
            current_node.content += current_char
            if current_char == ':':
                current_node.type = NodeType.CONFIG

        index += 1

    return tree, index



def count_function_braces(input: str) -> tuple[int, int]:
    opening_brackets = 0
    closing_brackets = 0
    for i in range(0, len(input)):
        if input[i] == '[':
            opening_brackets += 1
        elif input[i] == ']':
            closing_brackets += 1
        else:
            continue

    return opening_brackets, closing_brackets                



def resolve_config_node(node: Node, configs: dict):
    # Find the pc content in configs
    section, option = node.content.split(':', 1)
    value = configs.get(section, {}).get(option, {})

    if value == {}:
        output.error(f"Node content: {node.content} cannot be resolved from config")
        globals.exit_mate(globals.ERROR_CODE)

    node.resolved = True
    node.value = value


def resolve_config_nodes(tree: list[Node], configs: dict):
    for node in tree:
        if node.type == NodeType.CONFIG and node.resolved == False:
            resolve_config_node(node, configs)




def node_children_values_to_list(node: Node) -> list[str]:
    ret_values = []
    for child in node.children:
        ret_values.append(child.value)
    return ret_values



def resolve_function_nodes(tree: list[Node], all_functions: dict[str, MateModule], execution_dir: Path):
    for node in sorted(tree, key=lambda n: n.depth, reverse=True):
        if node.type != NodeType.FUNCTION:
            continue
        node_args = node_children_values_to_list(node)
        value = all_functions[node.content].module.run(execution_dir, node_args)
        node.value = value


def resolve_argument(argument:str, placeholders: list[Node]) -> str:
    root_node = placeholders[0]

    if isinstance(root_node.value, list):
        end_value = ''.join(root_node.value)
    else:
        end_value = root_node.value
    
    start, end = find_pc_delimiters(argument)
    subst_arg = argument.replace(f"%{argument[start:end]}%", end_value)

    return subst_arg
