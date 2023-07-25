import yaml
import subprocess
import pathlib
import shutil
import platform
import argparse
import build_options

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

def copy_dolphin_files(dolphin_lua_core_dirname, release_dolphin_dirname):
    release_dolphin_dirpath = pathlib.Path(release_dolphin_dirname)
    release_dolphin_dirpath.mkdir(exist_ok=True, parents=True)

    dolphin_lua_core_binary_dirname = f"{dolphin_lua_core_dirname}/Binary/x64"

    print(f"Copying dolphin lua core to release directory!")

    for folder in lua_core_folders_to_copy:
        src_folder = pathlib.Path(f"{dolphin_lua_core_binary_dirname}/{folder}")
        if not src_folder.is_dir():
            raise RuntimeError(f"\"{dolphin_lua_core_binary_dirname}\" is not a valid path to the custom Dolphin-Lua-Core built for auto-tt-recorder!")
        shutil.copytree(src_folder, f"{release_dolphin_dirname}/{folder}")

    for file in lua_core_files_to_copy:
        src_file = pathlib.Path(f"{dolphin_lua_core_binary_dirname}/{file}")
        if not src_file.is_file():
            raise RuntimeError(f"\"{dolphin_lua_core_binary_dirname}\" is not a valid path to the custom Dolphin-Lua-Core built for auto-tt-recorder!")

        shutil.copy2(src_file, f"{release_dolphin_dirname}/{file}")

    print("Creating dolphin/portable.txt!")

    pathlib.Path(f"{release_dolphin_dirname}/portable.txt").touch()

    print("Copying Lua Scripts to release directory!")
    shutil.copytree("dolphin/Sys/Scripts", f"{release_dolphin_dirname}/Sys/Scripts")

def copy_bin_files(release_dirname):
    print("Copying binary files!")
    
    release_bin_dirname = f"{release_dirname}/bin"
    pathlib.Path(release_bin_dirname).mkdir(parents=True)

    for file in bin_files_to_copy:
        shutil.copy2(f"bin/{file}", f"{release_dirname}/bin/{file}")

def copy_wiimm_files(release_wiimm_dirname, platform_dirname):
    shutil.copytree(f"bin/wiimm/{platform_dirname}", f"{release_wiimm_dirname}/{platform_dirname}")

def main():
    platform_system_lower = platform.system().lower()

    #ap = argparse.ArgumentParser()
    #ap.add_argument("-g", "--for-gui", dest="for_gui", action="store_true", default=False, description="Whether to package auto-tt-recorder for GUI")
    #
    #ap.parse_args()

    options = build_options.open_options("build_options.yml")

    for_gui = options["for-gui"]

    print("Building record_ghost.exe!")
    package_type_flag = "-D" if for_gui else "-F"

    subprocess.run(("pyinstaller", package_type_flag, "--noconfirm", "record_ghost.py", "--paths", "virt_win/Lib/site-packages"), check=True)

    dolphin_lua_core_dirname = options["dolphin-lua-core-dirname"]
    release_name = options["release-name"]

    if for_gui:
        release_dirname = f"release_working/auto-tt-recorder_{release_name}_for_gui"
    else:
        release_dirname = f"release_working/{release_name}"

    print(f"Copying fixed release files to {release_dirname}")

    release_dirpath = pathlib.Path(release_dirname)
    if release_dirpath.is_dir():
        shutil.rmtree(release_dirpath)

    if for_gui:
        shutil.copytree("release/licenses", f"{release_dirpath}/licenses")
        shutil.copy2("release/legal.txt", f"{release_dirpath}/legal.txt")
        shutil.copy2("release/README_AND_HELP.txt", f"{release_dirpath}/README_AND_HELP.txt")
    else:
        shutil.copytree("release", release_dirpath)

    release_dirpath.mkdir(parents=True, exist_ok=True)
    release_dolphin_dirname = f"{release_dirname}/dolphin"
    copy_dolphin_files(dolphin_lua_core_dirname, release_dolphin_dirname)

    copy_bin_files(release_dirname)
    copy_wiimm_files(f"{release_dirname}/bin/wiimm", "cygwin64" if platform_system_lower == "windows" else "linux")

    print("Copying data and layout files!")
    shutil.copytree("data", f"{release_dirname}/data")
    shutil.copytree("layouts", f"{release_dirname}/layouts")

    if for_gui:
        print("Copying dist/record_ghost/ to release directory!")
        shutil.copytree("dist/record_ghost", f"{release_dirname}/bin/record_ghost")
    else:
        print("Copying record_ghost.exe to release directory!")
        shutil.copy2("dist/record_ghost.exe", f"{release_dirname}/bin/record_ghost.exe")

    sevenz_filename = options["sevenz-filename"]

    if not for_gui:
        print("Creating 7z archive!")
        seven_zip_filename = f"release_working/auto-tt-recorder_{release_name}.7z"
        seven_zip_filepath = pathlib.Path(seven_zip_filename)
        seven_zip_filepath.unlink(missing_ok=True)
    
        subprocess.run((sevenz_filename, "a", f"release_working/auto-tt-recorder_{release_name}.7z", f"./release_working/{release_name}/*", "-t7z", "-mx=9", "-myx=9", "-ms=on", "-mmt=off", "-m0=LZMA2:d=256m:fb=273:mc=10000"), check=True)
    
        print("Creating zip archive!")
        subprocess.run((sevenz_filename, "a", f"release_working/auto-tt-recorder_{release_name}.zip", f"./release_working/{release_name}/*", "-tzip", "-mx=9", "-mfb=258", "-mpass=3", "-mmt=off"), check=True)

if __name__ == "__main__":
    main()
