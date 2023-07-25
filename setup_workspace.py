import package_release
import build_options
import pathlib
import os
import shutil
import requests
from contextlib import contextmanager
import subprocess
import json
import glob

def decompress(compressed_filename, sevenz_filename):
    compressed_parent_dirname = str(pathlib.Path(compressed_filename).parent)
    subprocess.run((sevenz_filename, "x", compressed_filename, f"-o{compressed_parent_dirname}/*"), check=True)

TEMP_DIRNAME = "setup_temp"

@contextmanager
def temp_download_compressed_file(url, destination_dirname, sevenz_filename):
    toplevel_uncompressed_dirname = None
    compressed_filename = None

    try:
        if url.endswith(".tar.gz"):
            compressed_file_ext = ".tar.gz"
        elif url.endswith(".zip"):
            compressed_file_ext = ".zip"
        elif url.endswith(".7z"):
            compressed_file_ext = ".7z"
        else:
            raise RuntimeError()

        print(f"Downloading {destination_dirname} from {url}!")
        r = requests.get(url)
        pathlib.Path(TEMP_DIRNAME).mkdir(exist_ok=True, parents=True)
        compressed_filename = f"{TEMP_DIRNAME}/{destination_dirname}{compressed_file_ext}"
        toplevel_uncompressed_dirname = pathlib.Path(compressed_filename).with_suffix("")
        uncompressed_dirname = toplevel_uncompressed_dirname

        with open(compressed_filename, "wb+") as f:
            f.write(r.content)

        if compressed_file_ext == ".tar.gz":
            decompress(compressed_filename, sevenz_filename)
            tar_dirpath = pathlib.Path(compressed_filename).with_suffix("")
            tar_basename = tar_dirpath.name
            tar_filename = str(tar_dirpath / tar_basename)
            decompress(tar_filename, sevenz_filename)
            uncompressed_dirname = pathlib.Path(tar_filename).with_suffix("")
        else:
            decompress(compressed_filename, sevenz_filename)
            

        yield pathlib.Path(uncompressed_dirname)
    finally:
        shutil.rmtree(TEMP_DIRNAME)
        #if uncompressed_dirname is not None and pathlib.Path(toplevel_uncompressed_dirname).is_dir():
        #    shutil.rmtree(toplevel_uncompressed_dirname)
        #if compressed_filename is not None and pathlib.Path(compressed_filename).is_file():
        #    os.remove(compressed_filename)

def main():
    options = build_options.open_options("build_options.yml")
    dolphin_lua_core_dirname = options["dolphin-lua-core-dirname"]
    sevenz_filename = options["sevenz-filename"]

    dolphin_dirpath = pathlib.Path("dolphin")

    if not dolphin_dirpath.is_dir():
        raise RuntimeError("\"dolphin\" directory missing! Either corrupt install or deleted it (need the directory as lua scripts are saved there)")

    temp_dolphin_Sys_Scripts_dirpath = pathlib.Path(f"{TEMP_DIRNAME}/dolphin_Sys_Scripts")

    if temp_dolphin_Sys_Scripts_dirpath.is_dir():
        shutil.rmtree(temp_dolphin_Sys_Scripts_dirpath)
    elif temp_dolphin_Sys_Scripts_dirpath.is_file():
        temp_dolphin_Sys_Scripts_dirpath.unlink()
    else:
        pathlib.Path(TEMP_DIRNAME).mkdir(exist_ok=True, parents=True)

    dolphin_sys_scripts_dirpath = pathlib.Path("dolphin/Sys/Scripts")
    os.rename(dolphin_sys_scripts_dirpath, f"{TEMP_DIRNAME}/dolphin_Sys_Scripts")
    shutil.rmtree(dolphin_dirpath)
    dolphin_sys_scripts_dirpath.parent.mkdir(exist_ok=True, parents=True)
    os.rename(f"{TEMP_DIRNAME}/dolphin_Sys_Scripts", dolphin_sys_scripts_dirpath)

    package_release.copy_dolphin_files(dolphin_lua_core_dirname, "dolphin", False)

    with open("binary_sources.json", "r") as f:
        binary_sources = json.load(f)

    bin_dirpath = pathlib.Path("bin")
    if bin_dirpath.is_dir():
        ffmpeg_dest_filepath = bin_dirpath / "ffmpeg.exe"
        ffprobe_dest_filepath = bin_dirpath / "ffprobe.exe"
        ffmpeg_dest_filepath.unlink(missing_ok=True)
        ffprobe_dest_filepath.unlink(missing_ok=True)
    else:
        bin_dirpath.mkdir()

    ffmpeg_windows_url = binary_sources["ffmpeg-windows"]
    
    with temp_download_compressed_file(ffmpeg_windows_url, "ffmpeg-windows", sevenz_filename) as uncompressed_dirpath:
        ffmpeg_windows_root, ffmpeg_windows_dirs, ffmpeg_windows_files = next(os.walk(uncompressed_dirpath))

        if len(ffmpeg_windows_dirs) != 1:
            raise RuntimeError(f"Unexpected directory structure for extracted downloaded ffmpeg 7z file! (ffmpeg_windows_dirs: {ffmpeg_windows_dirs})")

        ffmpeg_bin_dirpath = uncompressed_dirpath / f"{ffmpeg_windows_dirs[0]}/bin"
        ffmpeg_src_filepath = ffmpeg_bin_dirpath / "ffmpeg.exe"
        ffprobe_src_filepath = ffmpeg_bin_dirpath / "ffprobe.exe"

        print("Copying over ffmpeg.exe and ffprobe.exe!")
        os.rename(ffmpeg_src_filepath, "bin/ffmpeg.exe")
        os.rename(ffprobe_src_filepath, "bin/ffprobe.exe")

    szs_tools_windows_url = binary_sources["szs-tools-windows"]

    wiimm_windows_dirpath = pathlib.Path("bin/wiimm/cygwin64")
    if wiimm_windows_dirpath.is_dir():
        for dll_file in glob.glob("bin/wiimm/cygwin64/*.dll"):
            os.remove(dll_file)
        pathlib.Path("bin/wiimm/cygwin64/wszst.exe").unlink(missing_ok=True)
        pathlib.Path("bin/wiimm/cygwin64/wkmpt.exe").unlink(missing_ok=True)
        pathlib.Path("bin/wiimm/cygwin64/wit.exe").unlink(missing_ok=True)
    else:
        wiimm_windows_dirpath.mkdir(parents=True)

    szs_tools_dll_basenames = set()

    with temp_download_compressed_file(szs_tools_windows_url, "szs-tools-windows", sevenz_filename) as uncompressed_dirpath:
        szs_tools_windows_root, szs_tools_windows_dirs, szs_tools_windows_files = next(os.walk(uncompressed_dirpath))

        if len(szs_tools_windows_dirs) != 1:
            raise RuntimeError(f"Unexpected directory structure for extracted downloaded szs tools zip file! (szs_tools_windows_dirs: {szs_tools_windows_dirs})")

        szs_tools_bin_dirpath = uncompressed_dirpath / f"{szs_tools_windows_dirs[0]}/bin"
        wszst_src_filepath = szs_tools_bin_dirpath / "wszst.exe"
        wkmpt_src_filepath = szs_tools_bin_dirpath / "wkmpt.exe"

        print(f"Copying over wszst.exe, wkmpt.exe, and dlls!")
        os.rename(wszst_src_filepath, "bin/wiimm/cygwin64/wszst.exe")
        os.rename(wkmpt_src_filepath, "bin/wiimm/cygwin64/wkmpt.exe")

        szs_tools_dll_files = glob.glob(f"{str(szs_tools_bin_dirpath)}/*.dll")
        for dll_file in szs_tools_dll_files:
            dll_basename = pathlib.Path(dll_file).name
            szs_tools_dll_basenames.add(dll_basename)
            os.rename(dll_file, f"bin/wiimm/cygwin64/{dll_basename}")

    wit_windows_url = binary_sources["wit-windows"]

    with temp_download_compressed_file(wit_windows_url, "wit-windows", sevenz_filename) as uncompressed_dirpath:
        wit_windows_root, wit_windows_dirs, wit_windows_files = next(os.walk(uncompressed_dirpath))

        if len(wit_windows_dirs) != 1:
            raise RuntimeError(f"Unexpected directory structure for extracted downloaded wit zip file! (wit_windows_dirs: {wit_windows_dirs})")

        print(f"wit_windows_dirs: {wit_windows_dirs}")

        wit_bin_dirpath = uncompressed_dirpath / f"{wit_windows_dirs[0]}/bin"
        wit_src_filepath = wit_bin_dirpath / "wit.exe"
        print(f"Copying over wit.exe and dlls!")
        os.rename(wit_src_filepath, "bin/wiimm/cygwin64/wit.exe")

        wit_dll_files = glob.glob(f"{str(wit_bin_dirpath)}/*.dll")
        wit_dll_basenames = {pathlib.Path(dll_filename).name for dll_filename in wit_dll_files}
        wit_unique_dll_files = wit_dll_basenames - szs_tools_dll_basenames
        for dll_file in wit_dll_files:
            dll_basename = pathlib.Path(dll_file).name
            if dll_basename not in wit_unique_dll_files:
                continue

            os.rename(dll_file, f"bin/wiimm/cygwin64/{dll_basename}")

    wiimm_linux_dirpath = pathlib.Path("bin/wiimm/linux")
    if wiimm_linux_dirpath.is_dir():
        pathlib.Path("bin/wiimm/linux/wszst").unlink(missing_ok=True)
        pathlib.Path("bin/wiimm/linux/wkmpt").unlink(missing_ok=True)
        pathlib.Path("bin/wiimm/linux/wit").unlink(missing_ok=True)
    else:
        wiimm_linux_dirpath.mkdir(parents=True)

    szs_tools_linux_url = binary_sources["szs-tools-linux"]

    with temp_download_compressed_file(szs_tools_linux_url, "szs-tools-linux", sevenz_filename) as uncompressed_dirpath:
        szs_tools_linux_root, szs_tools_linux_dirs, szs_tools_linux_files = next(os.walk(uncompressed_dirpath))

        szs_tools_linux_dirname = None

        for szs_tools_linux_dirname in szs_tools_linux_dirs:
            if szs_tools_linux_dirname.startswith("szs"):
                found_szs_tools_linux_dirname = szs_tools_linux_dirname

        if szs_tools_linux_dirname is None:
            raise RuntimeError(f"Unexpected directory structure for extracted downloaded szs tools zip file! (szs_tools_linux_dirs: {szs_tools_linux_dirs})")

        szs_tools_bin_dirpath = uncompressed_dirpath / f"{szs_tools_linux_dirname}/bin"
        wszst_src_filepath = szs_tools_bin_dirpath / "wszst"
        wkmpt_src_filepath = szs_tools_bin_dirpath / "wkmpt"

        print(f"Copying over linux wszst and wkmpt!")
        os.rename(wszst_src_filepath, "bin/wiimm/linux/wszst")
        os.rename(wkmpt_src_filepath, "bin/wiimm/linux/wkmpt")

    wit_linux_url = binary_sources["wit-linux"]

    with temp_download_compressed_file(wit_linux_url, "wit-linux", sevenz_filename) as uncompressed_dirpath:
        wit_linux_root, wit_linux_dirs, wit_linux_files = next(os.walk(uncompressed_dirpath))

        wit_linux_dirname = None

        for wit_linux_dirname in wit_linux_dirs:
            if wit_linux_dirname.startswith("wit"):
                found_wit_linux_dirname = wit_linux_dirname

        if wit_linux_dirname is None:
            raise RuntimeError(f"Unexpected directory structure for extracted downloaded szs tools zip file! (wit_linux_dirs: {wit_linux_dirs})")

        wit_bin_dirpath = uncompressed_dirpath / f"{wit_linux_dirname}/bin"
        wit_src_dirpath = wit_bin_dirpath / "wit"

        print(f"Copying over linux wit!")
        os.rename(wit_src_dirpath, "bin/wiimm/linux/wit")


if __name__ == "__main__":
    main()
