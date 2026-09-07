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
- placeholder functions should be able to execute shell commands. uc: mate copy -i file.txt -d %shell[$Get-ItemName]%.txt
-- UC: mate copy %shell[$Env:ANDROID_SDK_ROOT]/file.txt% 

Future work
Use Story
- Be able to execute an executable which not global and not part of the config (eg. mate c:\folder\someapp.exe somefile.txt) The current behaviour will try to execute a powershell command at the moment.
- I want to see a summary at the end of each execution if everything went well or if a folder had an error
- I want to perform a retry on a command if it hasnt been sucessfully executed on some of the folder. The retry should execute only those folders that didn't succeed the first time
- I want to specify the type of the executer (shell, global, config or module) if for some reason the command doesn't sent to the proper executer by the app or another executor with the same name exists which has priority over the desired
- I want to be able to modify the executor selection order. The default is currently hard coded and cannot be changed 

- I want to be able to define own modules in global or in local directory
-- REQ: The tool shall add default options of newly added modules upon discovering them
-- REQ: Mate shall not override any modified options from embedded commands. 


