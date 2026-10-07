

from mate import placeholderslib
from mate.placeholderslib import Node

from types import ModuleType
from collections.abc import Callable
from mate.utilities import MateModule

def create_mock_module(name: str, run_function: Callable,) -> ModuleType:
    module = ModuleType(name)
    module.run = run_function
    return module


# pc = "%f1[f2[],f3[],1,abc:config]%"
# # pc = "abc%f1,f2,f3%zyx" # This should be illegal, ONLY possible if parent is a function
# # pc = "%config:option%"
pc = "%string%"
pc = "prefix%function1[bca,func2[1,f23],abc]%suffix"


start, end = placeholderslib.find_pc_delimiters(pc)
print(f"start: {start}, end {end}")
print(f"{pc[start:end]}")

# pc_tree = []
pct   = placeholderslib.create_pc_tree(pc[start:end])

for node in pct:
    print(f"{node.index}/{node.id}:{node.depth} - {node.value} / {node.type}")


# depth_first_indices = placeholderslib.resolve_tree_functions(pct)

# print(f"depth_first_indices: {depth_first_indices}")

root = pct[0]
# print("--------------")
def print_tree(root: Node):
    print(f"{root.id}:{root.depth} - {root.content} / {root.type} -> {root.value}")
    for child in root.children:
        print(f"{child.id}:{child.depth} - {child.content} / {child.type} -> {child.value}")
        if len(child.children) != 0:
            print_tree(child)


# print_tree(root)


# o, c = placeholderslib.count_function_braces(pc)
# print (o)
# print(c)


configs = {
    "vars": {
        "var1" : "VAR1",
        "var2" : "VAR2",
        "o1" : "O1"
    }    
}


pc = "f[vars:var1,vars:o1]"

pc_tree2 = placeholderslib.create_pc_tree(pc)

placeholderslib.resolve_config_nodes(pc_tree2, configs)

print_tree(pc_tree2[0])

# node = Node(id=0, content="vars:var1")
# node2 = Node(id=0, content="vars:var13")
# placeholderslib.resolve_config_pc_content(node2, configs)

# print(f"node content:{node.content} -> {node.value}")
# test how to resolve the pc


args = ["none", "abc%func[]%", "NONE", "%func2[abc,func4[]]%avbc"]

args_pcs = placeholderslib.extract_argument_placeholders(args)

for arg, pct in args_pcs.items():
    print(f"{arg}")
    if pct != None:
        print_tree(pct[0])



def to_caps(cwd, args):
    ret_args = []
    for arg in args:
        ret_args.append(str(arg).capitalize())
    return ret_args


to_caps_modules = MateModule(
    path="folder.root.to_caps",
    module=create_mock_module("to_caps", to_caps),
)

def get_brach_name(cwd, args):
    return "feature-123"


get_brach_name_module = MateModule(
    path="folder.root.get_brach_name",
    module=create_mock_module("get_brach_name", get_brach_name),
)


def cwd_equal(cwd, args):
    return cwd == args[0]

cwd_equal_module = MateModule(
    path="folder.root.cwd_equal",
    module=create_mock_module("cwd_equal", cwd_equal),
)

pc = "to_caps[something,else,get_brach_name[]]"

pc_tree = placeholderslib.create_pc_tree(pc)
functions = {
    "to_caps" : to_caps_modules,
    "get_brach_name" : get_brach_name_module,
    "cwd_equal" : cwd_equal_module
}



placeholderslib.resolve_function_nodes(pc_tree,functions, ".")
print("end")
print_tree(pc_tree[0])

pc = "cwd_equal[something]"
pc_tree = placeholderslib.create_pc_tree(pc)

placeholderslib.resolve_function_nodes(pc_tree,functions, "someth_ing")
print(pc_tree[0].value)


test_tree = [Node(id=1,value="project")]

res_arg = placeholderslib.resolve_argument("%func[something]%_test.txt",test_tree)
print(res_arg)