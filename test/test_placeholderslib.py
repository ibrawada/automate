from typing import Tuple

from mate import placeholderslib


# pc = "prefix%function1[bca,func2[1,f23],abc]%suffix"
# pc = "%f1[f2[],f3[],1,abc:config]%"
# pc = "abc%f1,f2,f3%zyx" # This should be illegal, ONLY possible if parent is a function
pc = "%config:option%"
pc = "%string%"
def test_extract_pc():
    start, end = placeholderslib.find_pc_delimiters(pc)

  

# test_extract_pc()
start, end = placeholderslib.find_pc_delimiters(pc)
print(f"start: {start}, end {end}")
print(f"{pc[start:end]}")

pc_tree = []
pc_tree,_   = placeholderslib.create_pc_tree(pc[start:end],0,None,pc_tree)

for node in pc_tree:
    print(f"{node.id}:{node.level} - {node.value} / {node.type}")

# Write a recursive function that
# Extracts argument and also separates the 