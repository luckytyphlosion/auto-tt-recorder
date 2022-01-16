import json
from sortedcontainers import SortedList

PLAYER_ID = "EE91F250E359EC6E"

def main():
    with open("sorted_legacy_wrs.json", "r") as f:
        legacy_wrs = json.load(f)

    sorted_legacy_wrs = SortedList(legacy_wrs, key=lambda x: x["lastCheckedTimestamp"])
    output = ""

    for legacy_wr in sorted_legacy_wrs:
        if legacy_wr["ghostHref"] is not None and legacy_wr["playerId"] == PLAYER_ID and not legacy_wr["isRedundant"]:
            output += f"{legacy_wr['lbInfo']}\n"# Track Id: {legacy_wr['trackId']}, Full Track Name: {legacy_wr['trackNameFull']}\n"

    with open("player_legacy_wrs_out.txt", "w+") as f:
        f.write(output)

if __name__ == "__main__":
    main()
