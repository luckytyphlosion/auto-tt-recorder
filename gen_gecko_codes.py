# Copyright (C) 2022 luckytyphlosion
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import pathlib
from stateclasses.speedometer import *
import msgeditor
import identifiers
import re

try:
    import for_gui_module
    for_gui = True
except ImportError:
    for_gui = False

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

class LineReader:
    __slots__ = ("_line_num", "_lines", "_filename")
    def __init__(self, lines, filename):
        self._lines = lines
        self._filename = filename
        self._line_num = 0

    def __iter__(self):
        while self._line_num < len(self._lines):
            yield self._lines[self._line_num]
            self._line_num += 1

    def __getitem__(self, index):
        return self._lines[index]

    def __len__(self):
        return len(self._lines)

    @property
    def cur_line(self):
        return self._lines[self._line_num]

    def next(self):
        self._line_num += 1
        return self._lines[self._line_num]

    @property
    def line_num(self):
        return self._line_num

    @property
    def human_line_num(self):
        return self._line_num + 1

    def at_file_error(self, msg):
        raise RuntimeError(f"At {self._filename}:{self._line_num+1}: {msg}")

GECKO_SECTION_NONE = 0
GECKO_SECTION_GECKO = 1
GECKO_SECTION_GECKO_ENABLED = 2

gecko_header_regex = re.compile(r"^(?:\+.|\$)(.+?)(?:\[(.+?)(?:\]|$)|$)")
gecko_code_data_regex = re.compile(r"^[0-9A-Fa-f]{8}\s+[0-9A-Fa-f]{8}")

class GeckoCode:
    __slots__ = ("name", "author", "line_num", "contents", "invalid_lines")

    def __init__(self, name, author, line_num):
        self.name = name
        self.author = author
        self.line_num = line_num
        self.contents = []
        self.invalid_lines = {}

    def add_data(self, data, line_num):
        data = data.strip()
        if not gecko_code_data_regex.match(data):
            self.invalid_lines[line_num] = data

        self.contents.append(data)

    @staticmethod
    def try_make_gecko_code(potential_header_line, line_num):
        potential_header_line_startswith_plus = potential_header_line[0] == "+"
        if potential_header_line_startswith_plus or potential_header_line[0] == "$":
            match_obj = gecko_header_regex.match(potential_header_line)
            # can happen on "+." or "$"
            if match_obj is None:
                return GeckoCode("", "", line_num), potential_header_line_startswith_plus
            else:
                name = match_obj.group(1).strip()
                author = match_obj.group(2)
                if author is None:
                    author = ""
                return GeckoCode(name, author, line_num), potential_header_line_startswith_plus
        else:
            return None, False

class GeckoCodeConfigErrors:
    __slots__ = ("filename", "errors")

    def __init__(self, filename):
        self.filename = filename
        self.errors = {}

    def add(self, error, line_num):
        self.errors[line_num] = error

    def has_errors(self):
        return len(self.errors) != 0

    def gen_error_message(self, header_message):
        sorted_errors = sorted(self.errors.items(), key=lambda x: x[0])
        output = f"{header_message}:\n"
        output += "".join(f"  At line {line_num}: {error}\n" for line_num, error in sorted_errors)
        return output

class GeckoCodeConfig:
    __slots__ = ("gecko_codes", "gecko_enabled", "line_reader", "gecko_codes_to_enable", "gecko_code_config_filename", "missing_codes_to_enable")

    def __init__(self, gecko_code_config_filename, gecko_code_config_str=None):
        self.gecko_code_config_filename = gecko_code_config_filename
        if gecko_code_config_str is not None:
            lines = gecko_code_config_str.splitlines()
        else:
            gecko_code_config_filepath = pathlib.Path(gecko_code_config_filename)
            if gecko_code_config_filepath.suffix != ".ini":
                raise RuntimeError(f"Extra gecko codes filename must be .ini! (Got: {pathlib.Path(gecko_code_config_filename).suffix})")
            elif not gecko_code_config_filepath.is_file():
                raise RuntimeError(f"Could not find extra gecko codes file \"{gecko_code_config_filename}\"")

            with open(gecko_code_config_filename, "r") as f:
                lines = [line.rstrip("\n") for line in f.readlines()]

        self.line_reader = LineReader(lines, gecko_code_config_filename)
        self.gecko_codes = {}
        self.gecko_enabled = set()
        self.gecko_codes_to_enable = []
        self.missing_codes_to_enable = []
        self._parse_gecko_code_config()

    def _parse_gecko_code_config(self):
        errors = GeckoCodeConfigErrors(self.gecko_code_config_filename)

        gecko_section = GECKO_SECTION_NONE
        cur_gecko_code = None
        started_gecko_code_data_before_gecko_code_declared = False
        data_defined_before_section_declared = False
        line_reader = self.line_reader
        for line in line_reader:
            if line.strip() == "" or line[0] == "#":
                continue

            if line.startswith("[Gecko_Enabled]"):
                gecko_section = GECKO_SECTION_GECKO_ENABLED
                cur_gecko_code = None
            elif line.startswith("[Gecko]"):
                gecko_section = GECKO_SECTION_GECKO 
            else:
                if gecko_section == GECKO_SECTION_GECKO:
                    potential_gecko_code, is_enabled = GeckoCode.try_make_gecko_code(line, line_reader.human_line_num)
                    if potential_gecko_code is not None:
                        if potential_gecko_code.name == "":
                            errors.add(f"Gecko code was declared without a name (add a name after the {line[0] if line[0] == '$' else line[0:2]})", line_reader.human_line_num)
                        else:
                            existing_gecko_code = self.gecko_codes.get(potential_gecko_code.name)
                            if existing_gecko_code is not None:
                                errors.add(f"{potential_gecko_code.name} already defined at line {existing_gecko_code.line_num}", line_reader.human_line_num)
                            else:
                                self.gecko_codes[potential_gecko_code.name] = potential_gecko_code
                                if is_enabled:
                                    self.gecko_codes_to_enable.append((potential_gecko_code.name, line_reader.human_line_num))
                        cur_gecko_code = potential_gecko_code
                    elif line[0] != "*":
                        if cur_gecko_code is None:
                            if not started_gecko_code_data_before_gecko_code_declared:
                                started_gecko_code_data_before_gecko_code_declared = True
                                errors.add("Gecko code data defined before a gecko code was declared!", line_reader.human_line_num)
                        else:
                            cur_gecko_code.add_data(line, line_reader.human_line_num)
                elif gecko_section == GECKO_SECTION_GECKO_ENABLED:
                    if line[0] == "$":
                        gecko_code_name = line[1:]
                        self.gecko_codes_to_enable.append((gecko_code_name, line_reader.human_line_num))
                    else:
                        errors.add(f"Non-gecko code name \"{line}\" found in gecko code enabled section! (Add # at the start of the line to ignore)", line_reader.human_line_num)
                else:
                    if not data_defined_before_section_declared:
                        data_defined_before_section_declared = True
                        errors.add(f"Data \"{line}\" defined before either [Gecko_Enabled] or [Gecko] specified! (Add # at the start of the line to ignore)", line_reader.human_line_num)

        for gecko_code_name, line_num in self.gecko_codes_to_enable:
            if gecko_code_name in self.gecko_codes:
                self.gecko_enabled.add(gecko_code_name)
            else:
                self.missing_codes_to_enable.append((gecko_code_name, line_num))

        for gecko_code_name in self.gecko_enabled:
            gecko_code = self.gecko_codes[gecko_code_name]
            if len(gecko_code.invalid_lines) != 0:
                for line_num, invalid_line in gecko_code.invalid_lines.items():
                    errors.add(f"Bad gecko code data \"{invalid_line}\"!", line_num)

        if errors.has_errors():
            raise RuntimeError(errors.gen_error_message(f"Errors in gecko code file \"{errors.filename}\""))

    def merge(self, other_gecko_codes):
        errors = GeckoCodeConfigErrors(self.gecko_code_config_filename)
        other_gecko_code_names = set(other_gecko_codes.gecko_codes.keys())
        # error on duplicate gecko codes
        shared_gecko_code_names = set(self.gecko_codes.keys()) & other_gecko_code_names
        if len(shared_gecko_code_names) != 0:
            for shared_gecko_code_name in shared_gecko_code_names:
                line_num = self.gecko_codes[shared_gecko_code_name].line_num
                errors.add(f"\"Gecko code \"{shared_gecko_code_name}\" already exists in the autogenerated gecko code file! (either remove or rename the code name)", line_num)

        # trying to enable a gecko code defined in the template
        for missing_gecko_code_name, line_num in self.missing_codes_to_enable:
            if missing_gecko_code_name in other_gecko_code_names:
                errors.add(f"\"{missing_gecko_code_name}\" does not exist in the gecko code file but is enabling a code in the autogenerated gecko code file! (either remove or rename the code name)", line_num)

        if errors.has_errors():
            raise RuntimeError(errors.gen_error_message(f"Errors when merging {errors.filename} with the autogenerated gecko code file"))

        self.gecko_enabled.update(other_gecko_codes.gecko_enabled)
        for gecko_code_name, gecko_code in other_gecko_codes.gecko_codes.items():
            self.gecko_codes[gecko_code_name] = gecko_code

    def generate_output(self):
        output = ""
        output += "[Gecko]\n"
        for gecko_code_name, gecko_code in self.gecko_codes.items():
            output += f"${gecko_code_name}\n"
            output += "\n".join(gecko_code.contents) + "\n"

        output += "[Gecko_Enabled]\n"
        output += "".join(f"${gecko_code_name}\n" for gecko_code_name in self.gecko_enabled)
        return output

    @classmethod
    def from_filename(cls, gecko_code_config_filename):
        return cls(gecko_code_config_filename)

    @classmethod
    def from_string(cls, gecko_code_config_str, gecko_code_config_filename):
        return cls(gecko_code_config_filename, gecko_code_config_str=gecko_code_config_str)

def create_gecko_code_file(template_file, out_file, params, extra_gecko_codes):
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

    if extra_gecko_codes is not None:
        gecko_codes = GeckoCodeConfig.from_string(output, "autogenerated_codes.ini")
        extra_gecko_codes.merge(gecko_codes)
        output = extra_gecko_codes.generate_output()

    pathlib.Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w+") as f:
        f.write(output)

regular_km_h_som_num_decimal_places_to_xpos = {
    0: "c401",
    1: "c3f3",
    2: "c3ed"
}

def create_gecko_code_params(tt_character, tt_vehicle, default_drift, speedometer, disable_game_bgm, track_id, track_name, ending_message, on_200cc, region, no_background_blur, no_bloom):
    params = GeckoParams()

    params.add_subst("tt_character", tt_character)
    params.add_subst("tt_vehicle", tt_vehicle)
    # default_drift is True -> automatic -> 2 for gecko code
    # default_drift is False -> manual -> 1 for gecko code
    params.add_subst("default_drift", default_drift)

    if disable_game_bgm:
        params.enable_optional_code("$No Background Music")

    if speedometer.style == SOM_FANCY_KM_H:
        if speedometer.metric == SOM_METRIC_ENGINE:
            params.enable_optional_code("$Customizable Pretty Speedometer (Left Side)")
            params.add_subst("fancy_km_h_som_num_decimal_places", speedometer.decimal_places, num_digits=1)
        elif speedometer.metric in (SOM_METRIC_XYZ, SOM_METRIC_XZ):
            params.enable_optional_code("$Customizable Pretty XYZ Speedometer (Left Side)")
            params.add_subst("fancy_km_h_xyz_som_num_decimal_places", speedometer.decimal_places, num_digits=1)
        else:
            assert False
    elif speedometer.style == SOM_REGULAR_KM_H:
        if speedometer.metric == SOM_METRIC_ENGINE:
            params.enable_optional_code("$Customizable Pretty Speedometer with km/h text")
            params.add_subst("regular_km_h_som_num_decimal_places", speedometer.decimal_places, num_digits=1)
            params.add_subst("regular_km_h_som_xpos", regular_km_h_som_num_decimal_places_to_xpos[speedometer.decimal_places])
        elif speedometer.metric in (SOM_METRIC_XYZ, SOM_METRIC_XZ):
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

    if speedometer.metric in (SOM_METRIC_XYZ, SOM_METRIC_XZ):
        if speedometer.metric == SOM_METRIC_XYZ:
            xyz_or_xz_code = "ec21102a"
        elif speedometer.metric == SOM_METRIC_XZ:
            xyz_or_xz_code = "60000000"
        else:
            assert False
        params.add_subst("xyz_or_xz_metric", xyz_or_xz_code)

    msg_editor = msgeditor.MsgEditor(region.name)
    msg_editor.add_subst(identifiers.GHOST_CREATED_FOR_PLAYER_MSG_ID, ending_message)
    msg_editor.add_track_name_subst(track_id, track_name)
    msg_editor_code = msg_editor.generate()

    params.add_dynamic_code("$Msg Editor", msg_editor_code)

    if on_200cc:
        params.enable_optional_code("$CTGP 200cc")

    if no_background_blur:
        params.enable_optional_code("$No Background Blur")

    if no_bloom:
        params.enable_optional_code("$No Sun Filter")

    return params

def create_gecko_code_params_from_central_args(rkg, speedometer, disable_game_bgm, timeline_settings, track_name, ending_message, on_200cc, region, no_background_blur, no_bloom):
    tt_character = rkg.character_id
    tt_vehicle = rkg.vehicle_id
    default_drift = 2 if rkg.drift_type else 1

    return create_gecko_code_params(tt_character, tt_vehicle, default_drift, speedometer, disable_game_bgm, rkg.track_id, track_name, ending_message, on_200cc, region, no_background_blur, no_bloom)

def create_gecko_code_params_for_custom_top_10(rkg, timeline_settings, track_name, region, disable_game_bgm):
    custom_top_10_and_ghost_description = timeline_settings.custom_top_10_and_ghost_description

    params = GeckoParams()
    params.add_subst("custom_top_10_course_id", rkg.track_id)

    if disable_game_bgm:
        params.enable_optional_code("$No Background Music")

    if custom_top_10_and_ghost_description.globe_location == "ww":
        params.add_subst("custom_top_10_area", 2)
    else:
        params.add_subst("custom_top_10_area", 1)

    ghost_description = custom_top_10_and_ghost_description.ghost_description
    if ghost_description is None:
        ghost_description = "Ghost Data"

    msg_editor = msgeditor.MsgEditor(region.name)
    msg_editor.add_subst(identifiers.MY_GHOST_MSG_ID, ghost_description)
    # Todo, multiple language support
    msg_editor.add_subst(identifiers.MKCHANNEL_GHOST_SCREEN_RACE_THIS_GHOST_MSG_ID, "Start This Race")
    if for_gui:
        watch_replay_msg = "Watch the Replay"
    else:
        watch_replay_msg = "Watch Replay"

    msg_editor.add_subst(identifiers.MKCHANNEL_GHOST_SCREEN_WATCH_REPLAY_MSG_ID, watch_replay_msg)

    msg_editor.add_track_name_subst(rkg.track_id, track_name)
    msg_editor_code = msg_editor.generate()

    params.add_dynamic_code("$Custom Top 10", custom_top_10_and_ghost_description.top_10_code)
    params.add_dynamic_code("$Msg Editor", msg_editor_code)

    return params

def main():
    pass

if __name__ == "__main__":
    main()
