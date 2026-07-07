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