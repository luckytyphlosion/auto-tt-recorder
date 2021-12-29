import pathlib

class GeckoParams:
    __slots__ = ("substitutions", "optional_enabled_codes")

    def __init__(self):
        self.substitutions = []
        self.optional_enabled_codes = set()

    def add_subst(self, name, value):
        self.substitutions.append(GeckoSubst(name, value))

    def enable_optional_code(self, code_name):
        self.optional_enabled_codes.add(code_name)

class GeckoSubst:
    __slots__ = ("name", "value")

    def __init__(self, name, value):
        self.name = f"{{{name}}}"
        self.value = f"{value:02x}"

    def sub(self, line):
        return line.replace(self.name, self.value)

def create_gecko_code_file(template_file, out_file, params):
    with open(template_file, "r") as f:
        template_lines = f.readlines()

    substitutions = params.substitutions
    optional_enabled_codes = params.optional_enabled_codes

    for i, line in enumerate(template_lines):
        if line.strip() == "":
            continue
        elif line[0] in ("[", "$", "*"):
            continue

        # dumb algorithm but whatever
        for substitution in substitutions:
            if not ("{" in line and "}" in line):
                break

            line = substitution.sub(line)

        template_lines[i] = line
        
    output = "".join(template_lines)
    output += "\n".join(optional_enabled_codes)

    pathlib.Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w+") as f:
        f.write(output)

def create_gecko_code_params(default_character, default_vehicle, default_drift, no_music):
    params = GeckoParams()

    params.add_subst("default_character", default_character)
    params.add_subst("default_vehicle", default_vehicle)
    # default_drift is True -> automatic -> 2 for gecko code
    # default_drift is False -> manual -> 1 for gecko code
    params.add_subst("default_drift", default_drift)

    if no_music:
        params.enable_optional_code("$No Background Music")

    return params

def create_gecko_code_params_from_rkg(rkg, no_music):
    return create_gecko_code_params(rkg.character_id, rkg.vehicle_id, 2 if rkg.drift_type else 1, no_music)

def main():
    pass

if __name__ == "__main__":
    main()
