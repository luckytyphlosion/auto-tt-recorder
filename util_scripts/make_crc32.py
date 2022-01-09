def make_crc32_table():
    crc_table = []
    for n in range(256):
        c = n
        for k in range(8):
            c = 0xEDB88320 ^ (c >> 1) if c & 1 == 1 else c >> 1

        crc_table.append(c)

    output = ""
    output += "crc32_table = [\n"
    for i in range(32):
        output += "    " + ", ".join(f"0x{c:08x}" for c in crc_table[i*8:i*8+8]) + ", \n"

    output += "]\n"
    with open("make_crc32_out.txt", "w+") as f:
        f.write(output)

if __name__ == "__main__":
    make_crc32_table()
