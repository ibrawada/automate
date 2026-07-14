# Automate Tool

A tool to run operations across multiple project folders.

## Installation

```bash
pip install .
```

This will install the `automate` command.

## Config files
automate will create a global config file which will be located (under windows) in C:\Users\<user>\.mate\.mate-global.conf and a local config in the working directory .mate/mate-local.conf


### Content of config files
Both config files (global and local) will be loaded with each call to mate executable. First the global config will be called, then the local. This means that the section entries which are not extendable will be overwritten by local configs if they are present in the global config as well.

### Sections and entries
Important note, some sections are created by mate and should not be manually modified
- [folders] excludes: This will contain a list of folders to be excluded by mate during operation. This is an extendable entry
- 
# REQ
Fallback strategies. The list goes from top to bottom, when one candidate is found, then it is executed
- call to embedded commands (python scripts inside mate),
- call to local user commands (python scripts on users PC)
- call to config defined executables
- call to globally available executables
- call to shell commands
## Feature
- Be able to execute terminal custom commands eg. mkdir or something

REQ
- placeholder functions should be able to execute shell commands. uc: mate copy -i file.txt -d %shell[Get-ItemName]%.txt
