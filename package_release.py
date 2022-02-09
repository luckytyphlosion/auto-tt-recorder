import yaml
import subprocess
import pathlib
import shutil
import platform

lua_core_folders_to_copy = (
    "Languages",
    "Sys/GameSettings",
    "Sys/GC",
    "Sys/InfoDisplay",
    "Sys/Maps",
    "Sys/Resources",
    "Sys/Shaders",
    "Sys/Themes",
    "Sys/Wii"
)

lua_core_files_to_copy = (
    "Dolphin.exe",
    "lua5.3.dll",
    "OpenAL32.dll",
    "Sys/codehandler.bin",
    "Sys/totaldb.dsy"
)

bin_files_to_copy = (
    "ffmpeg.exe",
    "ffprobe.exe"
)

def main():
    platform_system_lower = platform.system().lower()

    with open("release_config.yml", "r") as f:
        release_config = yaml.safe_load(f)

    print("Building record_ghost.exe!")
    subprocess.run(("pyinstaller", "-F", "record_ghost.py"), check=True)

    dolphin_lua_core_dirname = release_config["dolphin_lua_core_dirname"]
    release_name = release_config["release_name"]

    release_dirname = f"release_working/{release_name}"
    print(f"Copying fixed release files to {release_dirname}")

    release_dirpath = pathlib.Path(release_dirname)
    if release_dirpath.is_dir():
        shutil.rmtree(release_dirpath)

    shutil.copytree("release", release_dirpath)

    release_dirpath.mkdir(parents=True, exist_ok=True)
    release_dolphin_dirname = f"{release_dirname}/dolphin"
    dolphin_lua_core_binary_dirname = f"{dolphin_lua_core_dirname}/Binary/x64"

    print(f"Copying dolphin lua core to release directory!")

    for folder in lua_core_folders_to_copy:
        shutil.copytree(f"{dolphin_lua_core_binary_dirname}/{folder}", f"{release_dolphin_dirname}/{folder}")

    for file in lua_core_files_to_copy:
        shutil.copy2(f"{dolphin_lua_core_binary_dirname}/{file}", f"{release_dolphin_dirname}/{file}")

    print("Creating dolphin/portable.txt!")

    pathlib.Path(f"{release_dolphin_dirname}/portable.txt").touch()

    print("Copying binary files!")
    
    release_bin_dirname = f"{release_dirname}/bin"
    pathlib.Path(release_bin_dirname).mkdir(parents=True)

    for file in bin_files_to_copy:
        shutil.copy2(f"bin/{file}", f"{release_dirname}/bin/{file}")

    if platform_system_lower == "windows":
        shutil.copytree(f"bin/wiimm/cygwin64", f"{release_dirname}/bin/wiimm/cygwin64")
    else:
        shutil.copytree(f"bin/wiimm/linux", f"{release_dirname}/bin/wiimm/linux")

    print("Copying data and layout files!")
    shutil.copytree("data", f"{release_dirname}/data")
    shutil.copytree("layouts", f"{release_dirname}/layouts")

    print("Copying record_ghost.exe to release directory!")
    shutil.copy2("dist/record_ghost.exe", f"{release_dirname}/bin/record_ghost.exe")

    print("Copying Lua Scripts to release directory!")
    shutil.copytree("dolphin/Sys/Scripts", f"{release_dolphin_dirname}/Sys/Scripts")

    print("Creating 7z archive!")
    seven_zip_filename = f"release_working/auto-tt-recorder_{release_name}.7z"
    seven_zip_filepath = pathlib.Path(seven_zip_filename)
    seven_zip_filepath.unlink(missing_ok=True)

    subprocess.run(("C:/Program Files/7-Zip/7z.exe", "a", f"release_working/auto-tt-recorder_{release_name}.7z", f"./release_working/{release_name}/*", "-t7z", "-mx=9", "-myx=9", "-ms=on", "-mmt=off", "-m0=LZMA2:d=256m:fb=273:mc=10000"), check=True)

    print("Creating zip archive!")
    subprocess.run(("C:/Program Files/7-Zip/7z.exe", "a", f"release_working/auto-tt-recorder_{release_name}.zip", f"./release_working/{release_name}/*", "-tzip", "-mx=9", "-mfb=258", "-mpass=15", "-mmt=off"), check=True)

if __name__ == "__main__":
    main()
