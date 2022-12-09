import chadsoft
import util
import identifiers
import re

vehicle_names = {
    0x15: "Bullet Bike",
    0x16: "Flame Runner",
    0x17: "Mach Bike"
}

finish_time_regex = re.compile(r"^([0-9]{2}):([0-9]{2})\.([0-9]{3})$")

def get_all_tops_for_leaderboard_list(leaderboards, num_tops=10):
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
        ghosts = {}
        for vehicle_id in (None, 0x15, 0x16, 0x17):
            leaderboard = chadsoft.get_lb_from_href(leaderboard_small["_links"]["item"]["href"], start=0, limit=1, vehicle=vehicle_id, read_cache=True, write_cache=True)
            if len(leaderboard["ghosts"]) != 0:
                ghost = leaderboard["ghosts"][0]
                if vehicle_id is None:
                    real_vehicle_id = ghost["vehicleId"]
                    if real_vehicle_id not in ghosts:
                        ghosts[real_vehicle_id] = ghost

                    ghosts[real_vehicle_id]["isWr"] = True
                else:
                    if vehicle_id not in ghosts:
                        ghost["isWr"] = False
                        ghosts[vehicle_id] = ghost
        
        for vehicle_id, ghost in ghosts.items():
            match_obj = finish_time_regex.match(ghost["finishTimeSimple"])
            minutes, seconds, milliseconds = int(match_obj.group(1)), int(match_obj.group(2)), int(match_obj.group(3))
            finish_time = util.min_sec_ms_to_time(minutes, seconds, milliseconds)
            ghost["finishTimeNumeric"] = finish_time

        sorted_ghosts = sorted(ghosts.items(), key=lambda x: x[1]["finishTimeNumeric"])

        for vehicle_id, ghost in sorted_ghosts:
            vehicle_name = identifiers.vehicle_names[vehicle_id]
            finish_time = ghost["finishTimeNumeric"]
            is_wr = ghost["isWr"]
            wr_str = " (WR)" if is_wr else "     "
            output += f"{vehicle_name:12}{wr_str}: {ghost['finishTimeSimple']}"
            vs_other_vehicles = []
            for vehicle_id2, ghost2 in sorted_ghosts:
                if vehicle_id == vehicle_id2:
                    continue

                vehicle_name2 = identifiers.vehicle_names[vehicle_id2]
                finish_time2 = ghost2["finishTimeNumeric"]
                if finish_time < finish_time2:
                    percentage = ((finish_time2 - finish_time)/finish_time) * 100
                    descriptor = "faster"
                else:
                    percentage = ((finish_time - finish_time2)/finish_time) * 100
                    descriptor = "slower"
                    
                vs_other_vehicles.append(f"vs {vehicle_name2}: {percentage:.3f}% {descriptor}")

            output += " (" + ", ".join(vs_other_vehicles) + ")\n"

        output += "\n"

    return output

def main():
    VEHICLE = 0x15

    output = ""

    original_track_leaderboards, status_code = chadsoft.get("/original-track-leaderboards.json", read_cache=True, write_cache=True)
    output += get_all_tops_for_leaderboard_list(original_track_leaderboards, num_tops=1)

    #original_track_leaderboards_200cc, status_code = chadsoft.get("/original-track-leaderboards-200cc.json", read_cache=True, write_cache=True)
    #output += get_all_tops_for_leaderboard_list(original_track_leaderboards_200cc, num_tops=1)

    ctgp_leaderboards, status_code = chadsoft.get("/ctgp-leaderboards.json", read_cache=True, write_cache=True)
    output += get_all_tops_for_leaderboard_list(ctgp_leaderboards, num_tops=1)

    #ctgp_200cc_leaderboards, status_code = chadsoft.get("/ctgp-leaderboards-200cc.json", read_cache=True, write_cache=True)
    #output += get_all_tops_for_leaderboard_list(ctgp_200cc_leaderboards, num_tops=1)

    with open("compare_mach_bullet_flame_out.dump", "w+") as f:
        f.write(output)

if __name__ == "__main__":
    main()
