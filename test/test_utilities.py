from mate import utilities

import os
from pathlib import Path


# def test_collect_modules():
p = Path(os.path.join("test_modules", "conditions", "git"))
# files = p.glob("*.py")
# for f in files: 
#     print(f)
# # print(files)
modules = utilities.collect_modules(Path(os.path.join("test_modules", "conditions")))
print(modules)


utilities.load_modules(modules)

for _,module in modules.items():
    print(module.module.run(Path('.'), ["args"]))

