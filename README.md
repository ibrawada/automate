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
- (Done/Partial)Be able to execute terminal custom commands eg. mkdir or something

REQ
- placeholder functions should be able to execute shell commands. uc: mate copy -i file.txt -d %shell[$Get-ItemName]%.txt
-- UC: mate copy %shell[$Env:ANDROID_SDK_ROOT]/file.txt% 

Future work
Use Story
- Be able to execute an executable which not global and not part of the config The current behaviour will try to execute a powershell command at the moment.
-- UC: mate c:\folder\someapp.exe somefile.txt
- I want to see a summary at the end of each execution if everything went well or if a folder had an error
-- Done(PARTIAL):
--- (Not yet implemented) REQ If during execution an exception or an error was thrown -> then this error shall be caught and execution continued for remaining folders
---- Of course this shall be context dependent: if for example a wrong application name provided eg. gti instead of git -> then execution shall break for everything because it doesnt make sense to continue
- I want to perform a retry on a command if it hasnt been sucessfully executed on some of the folder. The retry should execute only those folders that didn't succeed the first time
-- Done
--- Added a --start-from CLI argument to specify the folder from which the execution shall start. Skipping all the (sorted) folders in the list before start-folder

- I want to specify the type of the executer (shell, global, config or module) if for some reason the command doesn't sent to the proper executer by the app or another executor with the same name exists which has priority over the desired
- I want to be able to modify the executor selection order. The default is currently hard coded and cannot be changed 

- I want to be able to define own modules in global or in local directory
-- REQ: The tool shall add default options of newly added modules upon discovering them
-- REQ: Mate shall not override any modified options from embedded commands. 


- I want to be able to perform a set of operations on folders that originally fulfill specific condition
-- UC: perform any git operations on folders that initially had modifications. eg. Create a new branch, git add, git commit etc.. only for those repos.

- For a function placeholder i want to be able to read text from a file and use it as input.
-- gitea create-pr --description %read_file[<some_file>.txt]%