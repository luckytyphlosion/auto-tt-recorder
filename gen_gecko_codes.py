
class GeckoParam:
    __slots__ = ("name", "value")

    def __init__(self, name, value):
        self.name = f"{{{name}}}"
        self.value = f"{value:02x}"

    def sub(self, line):
        return line.replace(self.name, self.value)

def create_gecko_code_file(template_file, out_file, params):
    with open(template_file, "r") as f:
        template_lines = f.readlines()

    for i, line in enumerate(template_lines):
        if line.strip() == "":
            continue
        elif line[0] in ("[", "$", "*"):
            continue

        # dumb algorithm but whatever
        for param in params:
            if not ("{" in line and "}" in line):
                break

            line = param.sub(line)

        template_lines[i] = line

    output = "".join(template_lines)

    with open(out_file, "w+") as f:
        f.write(output)

def create_gecko_code_params(default_character, default_vehicle, default_drift):
    params = []
    params.append(GeckoParam("default_character", default_character))
    params.append(GeckoParam("default_vehicle", default_vehicle))
    # default_drift is True -> automatic -> 2 for gecko code
    # default_drift is False -> manual -> 1 for gecko code
    params.append(GeckoParam("default_drift", default_drift))

    return params

def create_gecko_code_params_from_rkg(rkg):
    return create_gecko_code_params(rkg.character_id, rkg.vehicle_id, 2 if rkg.drift_type else 1)

def main():
    pass

if __name__ == "__main__":
    main()
