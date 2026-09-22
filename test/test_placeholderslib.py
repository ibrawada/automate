from typing import Tuple

from mate import placeholderslib


pc = "function1[bca,func2[1,f23],abc]"

def check_matching_brackets_number(pc: str) -> bool:
    # count all [ and ]
    # return true if equal else error/Exception
    pass

def find_func_start(pc: str) -> Tuple[int, int]:
    # Appy several checks, that start+1 exist and len-1 == ] 
    start = pc.find('[') + 1
    end = len(pc)-1
    return (start, end)

print(find_func_start(pc))

f2_start, f2_end = find_func_start(pc)
f2 = pc[f2_start:f2_end]
print(pc[f2_start:f2_end])

f3s, f3e = find_func_start(f2)

print(f3s)
print(f3e)


# Write a recursive function that
# Extracts argument and also separates the 