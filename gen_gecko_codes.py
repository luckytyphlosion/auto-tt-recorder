import pathlib
from stateclasses.speedometer import *
import msgeditor
import identifiers

class GeckoParams:
    __slots__ = ("substitutions", "optional_enabled_codes", "dynamic_codes")

    def __init__(self):
        self.substitutions = []
        self.optional_enabled_codes = set()
        self.dynamic_codes = []

    def add_subst(self, name, value, num_digits=2):
        self.substitutions.append(GeckoSubst(name, value, num_digits))

    def enable_optional_code(self, code_name):
        self.optional_enabled_codes.add(code_name)

    def add_dynamic_code(self, name, value):
        self.dynamic_codes.append(DynamicCode(name, value))

class DynamicCode:
    __slots__ = ("name", "value")

    def __init__(self, name, value):
        self.name = name
        self.value = value

    def format(self):
        return f"{self.name}\n{self.value}\n"

class GeckoSubst:
    __slots__ = ("name", "value")

    def __init__(self, name, value, num_digits=2):
        self.name = f"{{{name}}}"
        if type(value) == str:
            self.value = value
        else:
            self.value = f"{{:0{num_digits}x}}".format(value)

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
            if line.startswith("[Gecko_Enabled]"):
                template_lines[i] = "\n".join(dynamic_code.format() for dynamic_code in params.dynamic_codes) + "\n[Gecko_Enabled]\n"

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

regular_km_h_som_num_decimal_places_to_xpos = {
    0: "c401",
    1: "c3f3",
    2: "c3ed"
}

def create_gecko_code_params(default_character, default_vehicle, default_drift, speedometer, disable_game_bgm):
    params = GeckoParams()

    params.add_subst("default_character", default_character)
    params.add_subst("default_vehicle", default_vehicle)
    # default_drift is True -> automatic -> 2 for gecko code
    # default_drift is False -> manual -> 1 for gecko code
    params.add_subst("default_drift", default_drift)

    if disable_game_bgm:
        params.enable_optional_code("$No Background Music")

    if speedometer.style == SOM_FANCY_KM_H:
        if speedometer.metric == SOM_METRIC_ENGINE:
            params.enable_optional_code("$Customizable Pretty Speedometer (Left Side)")
            params.add_subst("fancy_km_h_som_num_decimal_places", speedometer.decimal_places, num_digits=1)
        elif speedometer.metric == SOM_METRIC_XYZ:
            params.enable_optional_code("$Customizable Pretty XYZ Speedometer (Left Side)")
            params.add_subst("fancy_km_h_xyz_som_num_decimal_places", speedometer.decimal_places, num_digits=1)
        else:
            assert False
    elif speedometer.style == SOM_REGULAR_KM_H:
        if speedometer.metric == SOM_METRIC_ENGINE:
            params.enable_optional_code("$Customizable Pretty Speedometer with km/h text")
            params.add_subst("regular_km_h_som_num_decimal_places", speedometer.decimal_places, num_digits=1)
            params.add_subst("regular_km_h_som_xpos", regular_km_h_som_num_decimal_places_to_xpos[speedometer.decimal_places])
        elif speedometer.metric == SOM_METRIC_XYZ:
            params.enable_optional_code("$Customizable Pretty XYZ Speedometer with km/h text")
            params.add_subst("regular_km_h_xyz_som_num_decimal_places", speedometer.decimal_places, num_digits=1)
            params.add_subst("regular_km_h_xyz_som_xpos", regular_km_h_som_num_decimal_places_to_xpos[speedometer.decimal_places])
        else:
            assert False
    elif speedometer.style == SOM_STANDARD:
        if speedometer.metric == SOM_METRIC_ENGINE:
            params.enable_optional_code("$Pretty Speedometer 2.0")
        else:
            params.enable_optional_code("$Pretty Speedometer (XYZ version)")

    return params

def create_gecko_code_params_from_central_args(rkg, speedometer, disable_game_bgm, timeline_settings):
    default_character = rkg.character_id
    default_vehicle = rkg.vehicle_id
    default_drift = 2 if rkg.drift_type else 1

    return create_gecko_code_params(default_character, default_vehicle, default_drift, speedometer, disable_game_bgm)

def create_gecko_code_params_for_custom_top_10(rkg, timeline_settings):
    custom_top_10_and_ghost_description = timeline_settings.custom_top_10_and_ghost_description

    params = GeckoParams()
    params.add_subst("custom_top_10_course_id", rkg.track_id)

    if custom_top_10_and_ghost_description.globe_location == "ww":
        params.add_subst("custom_top_10_area", 2)
    else:
        params.add_subst("custom_top_10_area", 1)

    track_msg_id = identifiers.MARIO_CIRCUIT_MSG_ID + rkg.track_id
    course_name = custom_top_10_and_ghost_description.course_name
    if course_name is None:
        # lazy
        course_name = identifiers.track_names[rkg.track_by_human_id]

    ghost_description = custom_top_10_and_ghost_description.ghost_description
    if ghost_description is None:
        ghost_description = "Ghost Data"

    msg_substs = (
        msgeditor.MsgSubst(identifiers.MY_GHOST_MSG_ID, ghost_description),
        msgeditor.MsgSubst(track_msg_id, course_name)
    )

    msg_editor = msgeditor.MsgEditor(msg_substs, "NTSC-U")
    msg_editor_code = msg_editor.generate()

    params.add_dynamic_code("$Custom Top 10", custom_top_10_and_ghost_description.top_10_code)
    params.add_dynamic_code("$Msg Editor", msg_editor_code)

    return params

def main():
    pass

if __name__ == "__main__":
    main()
