

from mate import placeholderslib
from mate.placeholderslib import Node


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
    print(f"{node.index}/{node.id}:{node.level} - {node.value} / {node.type}")


depth_first_indices = placeholderslib.traverse_tree_LRR(pct)

print(f"depth_first_indices: {depth_first_indices}")

root = pct[0]
# print("--------------")
def print_tree(root: Node):
    for child in root.children:
        print(f"{child.id}:{child.level} - {child.content} / {child.type} -> {child.value}")
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

placeholderslib.resolve_config_pcs(pc_tree2, configs)

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