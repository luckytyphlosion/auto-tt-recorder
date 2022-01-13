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

# Much of this code was derived from https://github.com/AtishaRibeiro/TT-Rec-Tools/tree/dev/msgeditor
# Below is said code's license

# MIT License
# 
# Copyright (c) 2020 AtishaRibeiro
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import util
import identifiers

msgeditor_region_dependent_codes = {
    "PAL": "C25CDDC8",
    "NTSC-U": "C25C12A8",
    "NTSC-J": "C25CD6A4",
    "NTSC-K": "C25BBD88"
}

class MsgSubst:
    __slots__ = ("msg_id", "msg_text")

    def __init__(self, msg_id, msg_text):
        self.msg_id = msg_id
        self.msg_text = msg_text

class MsgEditor:
    __slots__ = ("msg_substs", "iso_region", "code")

    def __init__(self, iso_region):
        self.code = []
        self.msg_substs = []
        self.iso_region = iso_region

    def add_subst(self, msg_id, msg_text):
        if msg_text is not None:
            self.msg_substs.append(MsgSubst(msg_id, msg_text))

    def add_track_name_subst(self, track_id, track_name):
        if track_name is not None:
            track_msg_id = identifiers.MARIO_CIRCUIT_MSG_ID + track_id
            self.msg_substs.append(MsgSubst(track_msg_id, track_name))

    def generate(self):
        if len(self.msg_substs) == 1:
            self.generate_single_code()
        elif len(self.msg_substs) > 1:
            self.generate_multiple_msg_replacements()
        else:
            return "\n"

        return self.place_code()

    def generate_single_code(self):
        self.code = [msgeditor_region_dependent_codes[self.iso_region], "XXXXXXXX", "7D6802A6", "YYYYYYYY"]
        msg_subst = self.msg_substs[0]

        msg_value_as_utf_16_hex = util.utf_16_hex(msg_subst.msg_text);
        msg_value_as_utf_16_hex_plus_pad = f"{msg_value_as_utf_16_hex}0000"
        data = msg_value_as_utf_16_hex_plus_pad + "0" * (len(msg_value_as_utf_16_hex_plus_pad) % 8)

        self.code.extend("".join(eight_digit_chunk) for eight_digit_chunk in util.grouper(data, 8))

        self.code[3] = f"48{(len(data) // 2) + 5:06x}"
    
        msg_id = msg_subst.msg_id
        self.code.extend((f"2C0E{msg_id:04x}", "40820008",
                            "7C6802A6", "90610020",
                            "7D6803A6"))

        if len(self.code) % 2 == 0:
            self.code.append("60000000")

        self.code.append("00000000");
        self.code[1] = f"{(len(self.code) // 2) - 1:08x}"

    def generate_multiple_msg_replacements(self):
        self.code = [msgeditor_region_dependent_codes[self.iso_region], "XXXXXXXX", "7D6802A6", "YYYYYYYY"]
    
        # insert all the strings
        string_lengths = []
        data = ""
        
        for msg_subst in self.msg_substs:
            msg_value_as_utf_16_hex = util.utf_16_hex(msg_subst.msg_text)
            msg_value_as_utf_16_hex_plus_pad = f"{msg_value_as_utf_16_hex}0000"
            string_lengths.append(len(msg_value_as_utf_16_hex_plus_pad))
            data += msg_value_as_utf_16_hex_plus_pad

        # extend with zeros so the length becomes a multiple of 8
        data += "0" * (len(data) % 8)

        self.code.extend("".join(eight_digit_chunk) for eight_digit_chunk in util.grouper(data, 8))

        self.code[3] = f"48{(len(data) // 2) + 5:06x}"

        # actual code after the strings
        self.code.append("7D8802A6")
        string_offset = 0

        for msg_subst, string_length in zip(self.msg_substs, string_lengths):
            msg_id = msg_subst.msg_id
            self.code.extend((f"2c0e{msg_id:04x}", "40820008", f"386c{string_offset // 2:04x}"))
            string_offset += string_length

        self.code.extend(("90610020", "7D6803A6"));

        if len(self.code) % 2 == 0:
            self.code.append("60000000")

        self.code.append("00000000")
        self.code[1] = f"{(len(self.code) // 2) - 1:08x}"

    def place_code(self):
        return "".join(f"{code_part[0]} {code_part[1]}\n" for code_part in util.grouper(self.code, 2)).upper()

def main():

    msg_editor = MsgEditor("NTSC-U")
    msg_editor.add_subst(0x1398, "World Champion")
    msg_editor.add_subst(0x2458, "Sakura Sanctuary")

    msg_editor_code = msg_editor.generate()

    with open("msgeditor_out.dump", "w+") as f:
        f.write(msg_editor_code)

    msg_editor_2 = MsgEditor("NTSC-U")
    msg_editor_2.add_subst(0x045B, "Video recorded by Auto-TT-Recorder.")
    msg_editor_2_code = msg_editor_2.generate()

    with open("msgeditor2_out.dump", "w+") as f:
        f.write(msg_editor_2_code)

if __name__ == "__main__":
    main()

