# =============================================================================
# Copyright (c) 2022 luckytyphlosion
# 
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted.
# 
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
# AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
# INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
# LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
# OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.
# =============================================================================

def main():
    with open("avidump_pkts.dump", "r") as f:
        lines = f.readlines()

    state = 0
    start_frame = 2578
    start_pkts = 4

    for i, line in enumerate(lines, 1):
        line = line.strip()
        debug_info, msg = line.split("[Video]: ", maxsplit=1)
        if msg == "Start AVIDump loop":
            continue
        elif msg == "Stopping frame dump":
            break

        split_msg = msg.split(", ")

        cur_movie_frame = int(split_msg[0].replace("curMovieFrame: ", ""))
        cur_pkts = int(split_msg[1].replace("pkt.pts: ", ""))

        if cur_pkts - start_pkts != cur_movie_frame - start_frame:
            expected_frame = start_frame + cur_pkts - start_pkts
            print(f"Expected frame {expected_frame}, got {cur_movie_frame}!")

            start_pkts = cur_pkts
            start_frame = cur_movie_frame

if __name__ == "__main__":
    main()
