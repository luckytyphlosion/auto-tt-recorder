
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
