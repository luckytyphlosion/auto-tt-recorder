track_ids = {
    0x00: [4, 4],  0x01: [1, 1],  0x02: [2, 2],  0x03: [10, 11],
    0x04: [3, 3],  0x05: [5, 5],  0x06: [6, 6],  0x07: [7, 7],
    0x08: [0, 0],  0x09: [8, 8],  0x0A: [12, 13], 0x0B: [11, 10],
    0x0C: [14, 14], 0x0D: [15, 15], 0x0E: [13, 12], 0x0F: [9, 9],
    0x10: [24, 16], 0x11: [25, 27], 0x12: [26, 23], 0x13: [27, 30],
    0x14: [28, 17], 0x15: [29, 24], 0x16: [30, 29], 0x17: [31, 22],
    0x18: [18, 28], 0x19: [17, 18], 0x1A: [21, 19], 0x1B: [20, 20],
    0x1C: [23, 31], 0x1D: [22, 26], 0x1E: [19, 25], 0x1F: [16, 21]
}

def main():
    output = ""
    cur_col = 0

    for slot, track_id in track_ids.items():
        if cur_col == 0:
            output += "    "

        output += f"0x{slot:02x}: {track_id[1]}, "
        cur_col += 1
        if cur_col == 4:
            cur_col = 0
            output = output[:-1] + "\n"

    with open("gen_slot_to_human_id_out.txt", "w+") as f:
        f.write(output)

if __name__ == "__main__":
    main()
