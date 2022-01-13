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

import math

used_frames = set()

FPS = 59.94005994006

def main():
    with open("framedump_pts_2.dump", "r") as f:
        lines = f.readlines()

    expected_frame = 0

    for line in lines:
        line = line.strip()
        pts = float(line)
        pts_to_frame = round(pts * FPS)
        if not math.isclose(pts_to_frame, pts * FPS, rel_tol=0.0001):
            raise RuntimeError(f"Found bad pts {line}!")

        if pts_to_frame == expected_frame:
            expected_frame += 1
        else:
            print(f"expected frame {expected_frame}, got {pts_to_frame} ({line}) instead!")
            expected_frame = pts_to_frame + 1

if __name__ == "__main__":
    main()
