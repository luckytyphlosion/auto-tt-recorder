import import_ghost_to_save
import gen_gecko_codes
from gen_gecko_codes import GeckoParam
import create_lua_params
import subprocess
import pathlib
import time
import os

def main():
    franz = "01m41s1006378 Franz.rkg"
    cole = "01m08s7732250 Cole.rkg"
    iso_filename = "../../../RMCE01/RMCE01.iso"
    output_video_filename = "gv_bullet_bike_sc.mkv"

    bye_shun = "01m40s2989711 Bye shun.rkg"
    bigmactroy = "01m45s4056658 bigmactroy.rkg"

    niyake = "00m15s9610732 Niyake.rkg"
    niyake2 = "00m16s1320374 Niyake2.rkg"

    rkg_file_comparison = bigmactroy

    rkg, rkg_comparison = import_ghost_to_save.import_ghost_to_save(
        "rksys.dat", bye_shun,
        "dolphin/User/Wii/title/00010004/524d4345/data/rksys.dat",
        "dolphin/User/Wii/shared2/menu/FaceLib/RFL_DB.dat",
        rkg_file_comparison
    )

    params = gen_gecko_codes.create_gecko_code_params_from_rkg(rkg)
    gen_gecko_codes.create_gecko_code_file("RMCE01_gecko_codes_template.ini", "dolphin/User/GameSettings/RMCE01.ini", params)
    create_lua_params.create_lua_params(rkg, rkg_comparison, "dolphin/lua_config.txt")

    kill_path = pathlib.Path("dolphin/kill.txt")
    kill_path.unlink(missing_ok=True)

    framedump_path = pathlib.Path("dolphin/User/Dump/Frames/framedump0.avi")
    framedump_path.unlink(missing_ok=True)

    os.chdir("dolphin/")
    popen = subprocess.Popen(("./DolphinR.exe", "-b", "-hm", "-dr", "-e", iso_filename))
    kill_path = pathlib.Path("kill.txt")
    while True:
        if kill_path.is_file():
            popen.terminate()
            # wsl memes
            subprocess.run(("taskkill.exe", "/f", "/im", "DolphinR.exe"))
            break

        time.sleep(1)

    os.chdir("..")
    subprocess.run(
        ("ffmpeg", "-i", "dolphin/User/Dump/Frames/framedump0.avi", "-i", "dolphin/User/Dump/Audio/dspdump.wav", "-c", "copy", output_video_filename)
    )

    print("Done!")

def main2():
    popen = subprocess.Popen(("./dolphin/Dolphin.exe",))
    print(f"popen.pid: {popen.pid}")
    #time.sleep(5)
    #popen.terminate()

if __name__ == "__main__":
    main()
