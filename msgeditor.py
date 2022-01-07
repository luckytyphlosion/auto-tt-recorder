import util

msgeditor_region_dependent_codes = {
    "PAL": "C25CDDC8",
    "NTSC-U": "C25C12A8",
    "NTSC-J": "C25CD6A4",
    "NTSC-K": "C25BBD88"
}

# function generate_single_code() {
#     code = [ISO_CODES[ISO_REG], "XXXXXXXX",
#     "7D6802A6", "YYYYYYYY"];
# 
#     const [ret, error] = utf_16_hex(document.getElementById(`msg_input_0`).value);
#     if (ret == null) return `Wrong format for ${error}`;
#     var hex_string = ret + "0000";
#     hex_string += "0".repeat(hex_string.length % 8)
# 
#     for (var i = 0; i < hex_string.length; i += 8) {
#         code.push(hex_string.slice(i, i + 8));
#     }
# 
#     code[3] = "48" + pad((hex_string.length / 2) + 5, 6);
# 
#     var msg_id = get_msd_id(0);
#     if (msg_id == null) return "No ID filled in!";
#     code = code.concat([`2C0E${msg_id}`, "40820008",
#                         "7C6802A6", "90610020",
#                         "7D6803A6"])
# 
#     if (code.length % 2 == 0) code.push("60000000");
#     code.push("00000000");
#     code[1] = pad(code.length / 2 - 1, 8);
# 
#     return code;
# }

class MsgSubst:
    __slots__ = ("msg_id", "msg_text")

    def __init__(self, msg_id, msg_text):
        self.msg_id = msg_id
        self.msg_text = msg_text

class MsgEditor:
    __slots__ = ("msg_substs", "iso_region", "code")

    def __init__(self, msg_substs, iso_region):
        self.code = []
        self.msg_substs = msg_substs
        self.iso_region = iso_region

    def generate(self):
        self.generate_multiple_msg_replacements()
        return self.place_code()

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
            self.code.push("60000000")

        self.code.append("00000000")
        self.code[1] = f"{(len(self.code) // 2) - 1:08x}"

    def place_code(self):
        return "".join(f"{code_part[0]} {code_part[1]}\n" for code_part in util.grouper(self.code, 2)).upper()

def main():
    msg_substs = (
        MsgSubst(0x1398, "World Champion"),
        MsgSubst(0x2458, "Sakura Sanctuary")
    )

    msg_editor = MsgEditor(msg_substs, "NTSC-U")
    msg_editor_code = msg_editor.generate()

    with open("msgeditor_out.dump", "w+") as f:
        f.write(msg_editor_code)

if __name__ == "__main__":
    main()

