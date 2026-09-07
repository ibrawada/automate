# Mate Specification

## 1. Goal

## 2. Concepts
- Workspace
- Project folder
- Global config
- Local config
- Command
- Placeholder

## 3. Features

### Feature 1: Configuration
- User stories
- Requirements
- Acceptance criteria
- Open questions

### Feature 2: Placeholder Resolution
- User stories
- Requirements
- Acceptance criteria
- Open questions

### Feature 3: Command Resolution
- User stories
- Requirements
- Acceptance criteria
- Open questions

### Feature 4: Execution
- User stories
- Requirements
- Acceptance criteria
- Open questions

### Feature 5: Logging and Continue
- User stories
- Requirements
- Acceptance criteria
- Open questions


User stories
- As a dev i want to instructs mate which command type to execute so that it doesn't execute identically called and preferenced but wrong command type

# Have a config file to store values for each project
- Have a global config file which applies to every project
- Have a local config file for a specific project
- Upon execution the entries of global and local config files are merged 
- The entries of local config file override any identical entries from global file
- Certain config entries should be extendable and not overridable
- Upon start mate should check existance of global and local config file and create them with for mate required sections and entries

# Use place holders as CLI input parameters
- The place holders can be replaced by entries from global and local config files
- The place holders can be replaced by per folder generated variables
- If a place holder cannot be replaced, then an error message is output and execution is stopped
- Place holders can be separater by a space or next to each other
- Place holder starts and ends with a % character


# Mate config parameter processing
- a config parameter is created by using following syntax "mate config section:entry=value"
- a config parameter overwrites a previously existing value in the config if the value is non list item
- a config parameter extends the value list if the value is of type list
- a config parameter is written per default to local config file in the current execution directory
- a config parameter to extend the list can be added as a single item
TODO
- a cli entry can explicitely overwrite a list instead of extending if --override was provided
- a cli entry can remove a config parameter if --remove was provided 


# Execution of mate
- mate executes by provided command and arguments on each folder in the current working directory
- mate excludes folders from execution which are defined in folders.exclude list inside global and local config
- if an error occurs during execution, then the execution stops.
- mate stores the logs for all executions in a file. This file is replaced once a day
- mate can execute globally available executables 
- mate can execute executables defined inside a config file
- mate can execute python scripts
- mate can continue execution of after an error starting with the folder that threw the error (by providing --continue cli arg)
- mate can be instructed to execute a command of certain type and thus ignoring other types 