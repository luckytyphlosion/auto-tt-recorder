import chadsoft
import util
import identifiers

def get_all_tops_for_leaderboard_list(leaderboards, vehicle_id):
    output = ""
    #i = 0

    for leaderboard_small in leaderboards["leaderboards"]:
        track_name = leaderboard_small['name']
        category_id = leaderboard_small.get("categoryId")
        if category_id is not None:
            category_name = f"({identifiers.category_names_no_200cc[category_id]})"
        else:
            category_name = None
        str_200cc = "200cc" if leaderboard_small["200cc"] else None
        
        cc_200_track_category_name = util.join_conditional_modifier(str_200cc, track_name, category_name)
        print(f"Getting leaderboard for {cc_200_track_category_name}!")
        output += f"== {cc_200_track_category_name} ==\n"
        leaderboard = chadsoft.get_lb_from_href(leaderboard_small["_links"]["item"]["href"], start=0, limit=10, vehicle=vehicle_id, read_cache=True, write_cache=True)
        if len(leaderboard["ghosts"]) == 0:
            output += "<EMPTY>\n"
        else:
            for ghost in leaderboard["ghosts"]:
                output += f"{ghost['player']:10} - {ghost['finishTimeSimple']}\n"

        output += "\n"

    return output

def main():
    VEHICLE = 0x15

    output = ""

    original_track_leaderboards, status_code = chadsoft.get("/original-track-leaderboards.json", read_cache=True, write_cache=True)
    output += get_all_tops_for_leaderboard_list(original_track_leaderboards, VEHICLE)

    original_track_leaderboards_200cc, status_code = chadsoft.get("/original-track-leaderboards-200cc.json", read_cache=True, write_cache=True)
    output += get_all_tops_for_leaderboard_list(original_track_leaderboards_200cc, VEHICLE)

    ctgp_leaderboards, status_code = chadsoft.get("/ctgp-leaderboards.json", read_cache=True, write_cache=True)
    output += get_all_tops_for_leaderboard_list(ctgp_leaderboards, VEHICLE)

    ctgp_200cc_leaderboards, status_code = chadsoft.get("/ctgp-leaderboards-200cc.json", read_cache=True, write_cache=True)
    output += get_all_tops_for_leaderboard_list(ctgp_200cc_leaderboards, VEHICLE)

    with open("bullet_bike_tops_out.dump", "w+") as f:
        f.write(output)

if __name__ == "__main__":
    main()
