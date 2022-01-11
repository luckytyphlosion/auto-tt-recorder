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
