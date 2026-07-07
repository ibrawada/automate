# from mate.main import substitute_placeholders

# This should extract config and function place holders at the same time and return both lists
def extract_placeholders(input: str) -> tuple[list[str], list[str]]:
    config_placeholders = []
    function_placeholders = []
    
    start = -1
    placeholder = ""
    for i in range(0, len(input)):
        if input[i] == '%':
            # Start of placeholder found
            if start == -1:
                start = i
            # End of placeholder found
            else:
                placeholder = input[start+1:i]
                start = -1
        
                # Analyse if the placeholder is a config value or a function
                if '[' in placeholder and ']' in placeholder:
                    function_placeholders.append(placeholder)
                else:
                    config_placeholders.append(placeholder)

        # Detect error case -> if start has a value other than default and the end of arg parameter was reached 
        # this means that there was no end % 
    if start != -1:
        print(f"[ERROR] argument {input} has no ending % delimiter")
        # TODO throw an exception and break execution

    return (config_placeholders, function_placeholders)


def substitute_config_placeholders(input: str, placeholders: list[str], config_values: dict) -> list[str]:
    substituted_tokens = input

    for placehoder in placeholders:
        section, entry = placehoder.split(':')
        substituted_tokens = substituted_tokens.replace(f"%{placehoder}%", config_values[section][entry])

    return substituted_tokens




test = ['.\\test_basics.py', '"first=%env:a%"', 'arg:%env:b%', '%git.branch_name[]%%env:one%-%env:two%']
test2 = [ '%a%', '%b%']
configs = {
    "env":
    {
        "a": "A",
        "b": "B",
        "one": "ONE",
        "two" : "TWO"
    }
}

t = "%env:a%"

t2 = t.replace('%env:a%', "value")
print(t2)
arg_placeholders = {}
for arg in test:
    config_placeholders, function_placeholders = extract_placeholders(arg)
    arg_placeholders[arg]= {
            "config" : config_placeholders,
            "function" : function_placeholders
        }
    

for key, entries in arg_placeholders.items():
    config_placeholders = entries["config"]
    function_placeholders = entries["function"]
    subst_key = substitute_config_placeholders(key, config_placeholders, configs)
    print(subst_key)








    #     if arg.startswith('%') and ':' in arg:
    #         variable_name = arg[1:]
    #         section, key = variable_name.split(':', 1)
            
    #         # Safely get the value from the nested config dictionary
    #         value = configs.get(section, {}).get(key)
            
    #         if value is not None:
    #             substituted_args.append(str(value))
    #             print(f"Substituted '{arg}' with '{value}'")
    #         else:
    #             substituted_args.append(arg) # Keep original if not found
    #             # Variable not found in config, exit with an error
    #             print(f"Error: Variable '{arg}' not found in configuration.")
    #             # sys.exit(1)
    #     else:
    #         substituted_args.append(arg)
    # return substituted_args