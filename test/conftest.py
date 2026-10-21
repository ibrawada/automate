# The following modules are scratch scripts that execute code at import time (no assertions).
# Keep them out of pytest collection until they are converted into real tests.
collect_ignore = [
    "conanfile.py",
    "test_basics.py",
    "test_gitea.py",
    "test_main.py",
    "test_output.py",
    "test_placeholderslib.py",
    "test_replace.py",
    "test_shell.py",
    "test_utilities.py",
]
