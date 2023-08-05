import yaml
import subprocess
import pathlib
import random
import glob
import platform
import shutil
from wslpath import wslpath
import os
import sysconfig
from datetime import datetime, timezone

on_wsl = "microsoft" in platform.uname()[3].lower()
if on_wsl:
    python_name = "python3"
else:
    python_name = "python"

bin_dir = sysconfig.get_config_var("BINDIR")
python_filename = str(pathlib.Path(bin_dir, python_name))

import package_release
import build_options


on_windows = platform.system() == "Windows"

class RegionFilenameAndName:
    __slots__ = ("filename", "name")

    def __init__(self, filename, name):
        self.filename = filename
        self.name = name

region_names_except_selected = {
    "NTSC-U": ("PAL", "NTSC-J", "NTSC-K"),
    "PAL": ("NTSC-U", "NTSC-J", "NTSC-K"),
    "NTSC-J": ("NTSC-U", "PAL", "NTSC-K"),
    "NTSC-K": ("NTSC-U", "PAL", "NTSC-J")
}

TEST_MULTIPLE_REGIONS = False

RELEASE_CLEAN_INSTALL_YES = 0
RELEASE_CLEAN_INSTALL_RANDOM = 1
RELEASE_CLEAN_INSTALL_NO = 2

release_clean_install_option_to_enum = {
    True: RELEASE_CLEAN_INSTALL_YES,
    "random": RELEASE_CLEAN_INSTALL_RANDOM,
    False: RELEASE_CLEAN_INSTALL_NO
}

class AutoTTRecCmdFolder:
    __slots__ = ("name", "is_relative", "is_default")

    def __init__(self, name, is_relative=False, is_default=False):
        self.name = name
        self.is_relative = is_relative
        self.is_default = is_default

class AutoTTRecCmdFolders:
    __slots__ = ("name", "folders", "verification_func")

    def __init__(self, name, folders, verification_func=None):
        self.name = name
        self.folders = folders
        self.verification_func = verification_func

relative_folder_additives = [
    "data/extended_regions/../..",
    "test_ymls/..",
    "layouts/nunchuck/../.."
]

def is_storage_folder(storage_folder_name):
    storage_folder_dirpath = pathlib.Path(storage_folder_name)
    storage_root, storage_dirs, storage_files = next(os.walk(storage_folder_dirpath))
    extra_storage_folder_names = set(storage_dirs) - {"auto-add", "szs", "wbz"}

    if len(extra_storage_folder_names) != 0:
        raise RuntimeError(f"Provided storage folder \"{storage_folder_name}\" in test options contains extra directories! (extra directories detected: " + ", ".join(f"\"{extra_storage_folder_name}\"" for extra_storage_folder_name in extra_storage_folder_names))

def is_temp_folder(temp_folder_name):
    temp_folder_dirpath = pathlib.Path(temp_folder_name)
    temp_folder_size = temp_folder_dirpath.stat().st_size
    if temp_folder_size > 1073741824:
        raise RuntimeError(f"Sanity check: provided temp folder \"{temp_folder_name}\" is larger than 1GiB. Please manually clear it out in case there are important files there.")

def is_chadsoft_cached_folder(chadsoft_cached_folder_name):
    chadsoft_cached_dirpath = pathlib.Path(chadsoft_cached_folder_name)
    chadsoft_cached_root, chadsoft_cached_dirs, chadsoft_cached_files = next(os.walk(chadsoft_cached_dirpath))
    if len(chadsoft_cached_dirs) != 0:
        raise RuntimeError(f"Provided chadsoft cached folder \"{chadsoft_cached_folder_name}\" contains extra directories! (extra directories detected: " + ", ".join(f"\"{extra_chadsoft_cached_folder_name}\"" for extra_chadsoft_cached_folder_name in chadsoft_cached_dirs))

    chadsoft_cached_folder_errors = []

    for chadsoft_cached_filename in chadsoft_cached_files:
        if not chadsoft_cached_filename.startswith("%2F"):
            chadsoft_cached_folder_errors.append(f"  \"{chadsoft_cached_filename}\" does not start with %2F!\n")

        chadsoft_cached_filepath = pathlib.Path(chadsoft_cached_filename)
        if chadsoft_cached_filepath.suffix not in {".rkg", ".json"}:
            chadsoft_cached_folder_errors.append(f"  \"{chadsoft_cached_filename}\" is not rkg or json!\n")

    if len(chadsoft_cached_folder_errors) != 0:
        raise RuntimeError(f"Errors in contents of provided chadsoft cached folder \"{chadsoft_cached_folder_name}\":\n{''.join(chadsoft_cached_folder_errors)}")

auto_tt_rec_filename_cmds = [
    "main-ghost-auto",
    "comparison-ghost-auto",
    "main-ghost-filename",
    "comparison-ghost-filename",
    "szs-filename",
    "music-filename"
]

def main():
    if not on_wsl and not on_windows:
        raise RuntimeError("Test script currently only supports Windows!")

    pathlib.Path("temp").mkdir(exist_ok=True)
    pathlib.Path("test_vids").mkdir(exist_ok=True)

    options = build_options.open_options("build_options.yml")

    random_seed = options["randomize-tests-seed"]
    if random_seed != 0:
        random.seed(random_seed)
    
    test_config_include_indices = set(options["include-tests"])
    test_config_exclude_indices = set(options["exclude-tests"])

    iso_directory = options["iso-directory"]
    sevenz_filename = options["sevenz-filename"]

    storage_folder_absolute = options["storage-folder-absolute"]
    storage_folder_relative = options["storage-folder-relative"]
    storage_folder_relative_no_parent = options["storage-folder-relative-no-parent"]
    dolphin_folder_absolute = options["dolphin-folder-absolute"]
    dolphin_folder_relative = options["dolphin-folder-relative"]
    dolphin_folder_relative_no_parent = options["dolphin-folder-relative-no-parent"]
    temp_folder_relative = options["temp-folder-relative"]
    temp_folder_absolute = options["temp-folder-absolute"]
    temp_folder_relative_no_parent = options["temp-folder-relative-no-parent"]
    wiimm_folder_absolute = options["wiimm-folder-absolute"]
    wiimm_folder_relative = options["wiimm-folder-relative"]
    wiimm_folder_relative_no_parent = options["wiimm-folder-relative-no-parent"]

    extra_hq_textures_folder_absolute = options["extra-hq-textures-folder-absolute"]

    chadsoft_cache_folder_relative = options["chadsoft-cache-folder-relative"]
    chadsoft_cache_folder_relative_no_parent = options["chadsoft-cache-folder-relative-no-parent"]

    test_release = options["test-release"]
    #if test_release:
    #    print("Packaging release before testing!")
    #    subprocess.run((python_filename, "package_release.py"), check=True)

    release_clean_install = release_clean_install_option_to_enum[options["clean-install-on-test-release"]]

    force_delete_invalid_directories = options["force-delete-invalid-directories"]

    region_filenames_and_names = (
        RegionFilenameAndName(options["rmce01-iso"], "NTSC-U"),
        RegionFilenameAndName(options["rmcp01-iso"], "PAL"),
        RegionFilenameAndName(options["rmcj01-iso"], "NTSC-J"),
        RegionFilenameAndName(options["rmck01-iso"], "NTSC-K")
    )

    if on_wsl:
        iso_directory = wslpath(iso_directory)
        sevenz_filename = wslpath(sevenz_filename)

        storage_folder_absolute = wslpath(storage_folder_absolute)
        #storage_folder_relative = wslpath(storage_folder_relative)
        #storage_folder_relative_no_parent = wslpath(storage_folder_relative_no_parent)
        dolphin_folder_absolute = wslpath(dolphin_folder_absolute)
        #dolphin_folder_relative = wslpath(dolphin_folder_relative)
        #dolphin_folder_relative_no_parent = wslpath(dolphin_folder_relative_no_parent)
        #temp_folder_relative = wslpath(temp_folder_relative)
        temp_folder_absolute = wslpath(temp_folder_absolute)
        #temp_folder_relative_no_parent = wslpath(temp_folder_relative_no_parent)
        wiimm_folder_absolute = wslpath(wiimm_folder_absolute)
        #wiimm_folder_relative = wslpath(wiimm_folder_relative)
        #wiimm_folder_relative_no_parent = wslpath(wiimm_folder_relative_no_parent)
        extra_hq_textures_folder_absolute = wslpath(extra_hq_textures_folder_absolute)
        #chadsoft_cache_folder_relative_no_parent = wslpath(chadsoft_cache_folder_relative_no_parent)

    storage_folders = AutoTTRecCmdFolders("storage-folder", [
        AutoTTRecCmdFolder("storage", True, True),
        AutoTTRecCmdFolder(storage_folder_absolute),
        AutoTTRecCmdFolder(storage_folder_relative, True),
        AutoTTRecCmdFolder(storage_folder_relative_no_parent, True)
    ], verification_func=is_storage_folder)

    dolphin_folders = AutoTTRecCmdFolders("dolphin-folder", [
        AutoTTRecCmdFolder("dolphin", True, True),
        AutoTTRecCmdFolder(dolphin_folder_absolute),
        AutoTTRecCmdFolder(dolphin_folder_relative, True),
        AutoTTRecCmdFolder(dolphin_folder_relative_no_parent, True)
    ])

    temp_folders = AutoTTRecCmdFolders("temp-folder", [
        AutoTTRecCmdFolder("temp", True, True),
        AutoTTRecCmdFolder(temp_folder_absolute),
        AutoTTRecCmdFolder(temp_folder_relative, True),
        AutoTTRecCmdFolder(temp_folder_relative_no_parent, True)
    ], verification_func=is_temp_folder)

    wiimm_folders = AutoTTRecCmdFolders("wiimm-folder", [
        AutoTTRecCmdFolder("bin/wiimm", True, True),
        AutoTTRecCmdFolder(wiimm_folder_absolute),
        AutoTTRecCmdFolder(wiimm_folder_relative, True),
        AutoTTRecCmdFolder(wiimm_folder_relative_no_parent, True)
    ])

    extra_hq_textures_folders = AutoTTRecCmdFolders("extra-hq-textures-folder", [
        AutoTTRecCmdFolder(extra_hq_textures_folder_absolute)
    ])

    chadsoft_cache_folders = AutoTTRecCmdFolders("chadsoft-cache-folder", [
        AutoTTRecCmdFolder("chadsoft_cached", True, True),
        AutoTTRecCmdFolder(chadsoft_cache_folder_relative, True),
        AutoTTRecCmdFolder(chadsoft_cache_folder_relative_no_parent, True)
    ], verification_func=is_chadsoft_cached_folder)

    all_cmd_folders = [
        storage_folders,
        dolphin_folders,
        temp_folders,
        wiimm_folders,
        extra_hq_textures_folders,
        chadsoft_cache_folders
    ]

    dolphin_lua_core_dirname = options["dolphin-lua-core-dirname"]

    pathlib.Path("temp").mkdir(exist_ok=True, parents=True)

    if not options["assume-cmd-folders-exist"]:
        for dolphin_folder in dolphin_folders.folders:
            dolphin_dirpath = pathlib.Path(dolphin_folder.name)
            if dolphin_dirpath.is_dir():
                mkw_play_ghost_filepath = (dolphin_dirpath / "Sys/Scripts/_MKW_Play_Ghost.lua")
                #print(f"mkw_play_ghost_filepath: {mkw_play_ghost_filepath}, mkw_play_ghost_filepath.is_file(): {mkw_play_ghost_filepath.is_file()}")
                if mkw_play_ghost_filepath.is_file():
                    is_dolphin_folder = True
                    print(f"Removing dolphin folder \"{dolphin_folder.name}\"!")
                    if dolphin_folder.is_default:
                        dolphin_sys_scripts_dirpath = (dolphin_dirpath / "Sys/Scripts")
                        os.rename(dolphin_sys_scripts_dirpath, "temp/dolphin_Sys_Scripts")
                        shutil.rmtree(dolphin_dirpath)
                        dolphin_sys_scripts_dirpath.parent.mkdir(exist_ok=True, parents=True)
                        os.rename("temp/dolphin_Sys_Scripts", dolphin_sys_scripts_dirpath)
                    else:
                        shutil.rmtree(dolphin_dirpath)
                else:
                    if force_delete_invalid_directories:
                        print(f"Warning: \"{dolphin_folder.name}\" is not a dolphin folder, removing.")
                        shutil.rmtree(dolphin_dirpath)
                        is_dolphin_folder = True
                    else:
                        is_dolphin_folder = False
            elif dolphin_dirpath.exists():
                is_dolphin_folder = False
            else:
                is_dolphin_folder = True
    
            if not is_dolphin_folder:
                raise RuntimeError(f"Provided dolphin folder \"{dolphin_folder.name}\" in test options points to a non-dolphin folder!")
    
            print(f"Copying over source dolphin folder to \"{dolphin_folder.name}\"!")
            package_release.copy_dolphin_files(dolphin_lua_core_dirname, dolphin_folder.name, not dolphin_folder.is_default)
    
        for wiimm_folder in wiimm_folders.folders:
            if wiimm_folder.is_default:
                continue
    
            wiimm_dirpath = pathlib.Path(wiimm_folder.name)
            if wiimm_dirpath.is_dir():
                wiimm_root, wiimm_dirs, wiimm_files = next(os.walk(wiimm_dirpath))
                if len(set(wiimm_dirs) - {"cygwin64", "linux"}) != 0:
                    if force_delete_invalid_directories:
                        print(f"Warning: Provided wiimm folder \"{wiimm_folder.name}\" in test options points to a non-wiimm folder.")
                    else:
                        raise RuntimeError(f"Provided wiimm folder \"{wiimm_folder.name}\" in test options points to a non-wiimm folder!")
    
                missing_wiimm_dirs = {"cygwin64", "linux"} - set(wiimm_dirs)
            else:
                missing_wiimm_dirs = {"cygwin64", "linux"}

            for wiimm_dir in missing_wiimm_dirs:
                print(f"Copying over \"{wiimm_dir}\"-based wiimm tools to \"{wiimm_folder.name}\"!")
                package_release.copy_wiimm_files(wiimm_folder.name, wiimm_dir)
    
        for extra_hq_textures_folder in extra_hq_textures_folders.folders:
            if extra_hq_textures_folder is not None:
                extra_hq_textures_dirpath = pathlib.Path(extra_hq_textures_folder.name)
                if not extra_hq_textures_dirpath.is_dir():
                    raise RuntimeError(f"Provided extra hq textures folder \"{extra_hq_textures_folder.name}\" does not exist!")
    
        for autogenerated_folders in (storage_folders, temp_folders, chadsoft_cache_folders):
            print(f"Removing {autogenerated_folders.name} folders!")
            for autogenerated_folder in autogenerated_folders.folders:
                autogenerated_dirpath = pathlib.Path(autogenerated_folder.name)
                if autogenerated_dirpath.is_dir():
                    if autogenerated_folders.verification_func is not None:
                        try:
                            autogenerated_folders.verification_func(autogenerated_folder.name)
                        except RuntimeError as e:
                            if force_delete_invalid_directories:
                                print(f"Warning: {e}")
                            else:
                                raise e
    
                    print(f"Removing \"{autogenerated_folder.name}\"!")
                    shutil.rmtree(autogenerated_dirpath)
                elif autogenerated_dirpath.exists():
                    raise RuntimeError(f"Provided {autogenerated_folders.name} \"{autogenerated_folder.name}\" in test options is not a {autogenerated_folders.name}!")

    iso_dirpath = pathlib.Path(iso_directory)
    release_auto_tt_rec_basename = f"auto-tt-recorder_{options['release-name']}"
    release_auto_tt_rec_directory = f"release_working/{release_auto_tt_rec_basename}"
    release_auto_tt_rec_7z_filename = f"{release_auto_tt_rec_directory}.7z"

    test_config_include_indices_len = len(test_config_include_indices)

    test_result_output = ""

    if test_release:
        filename_folder_prefix = "../.."
    else:
        filename_folder_prefix = "./"

    config_filenames = glob.glob("test_ymls/*.yml")

    if random_seed != 0:
        random.shuffle(config_filenames)

    first_run = True
    datetime_now_str = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d_%I-%M-%p")

    for config_filename in config_filenames:
        config_basename = pathlib.Path(config_filename).name
        config_index = int(config_basename.split("_", maxsplit=1)[0])
        if test_config_include_indices_len != 0 and config_index not in test_config_include_indices:
            continue
        elif config_index in test_config_exclude_indices:
            continue

        with open(config_filename, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        output_video_filepath_extension = config["output-video-filename"]
        output_video_filepath_stem = pathlib.Path(config_basename).stem

        if TEST_MULTIPLE_REGIONS:
            cur_region_filenames_and_names = region_filenames_and_names
        else:
            cur_region_filenames_and_names = (random.choice(region_filenames_and_names),)
            #cur_region_filenames_and_names = (region_filenames_and_names[0],)

        for region_filename_and_name in cur_region_filenames_and_names:
            print(f"Testing region {region_filename_and_name.name}, config {config_basename}")

            for auto_tt_rec_filename_cmd in auto_tt_rec_filename_cmds:
                auto_tt_rec_filename_cmd_value = config.get(auto_tt_rec_filename_cmd)

                if auto_tt_rec_filename_cmd_value is not None:
                    modify_filename_cmd_value = True
    
                    if auto_tt_rec_filename_cmd in {"main-ghost-auto", "comparison-ghost-auto"}:
                        if auto_tt_rec_filename_cmd_value.endswith(".rkg"):
                            modify_filename_cmd_value = True
                        else:
                            modify_filename_cmd_value = False
                    elif auto_tt_rec_filename_cmd == "music-filename":
                        if auto_tt_rec_filename_cmd_value not in {"bgm", "none"}:
                            modify_filename_cmd_value = True
                        else:
                            modify_filename_cmd_value = False

                    if modify_filename_cmd_value:
                        auto_tt_rec_filename_cmd_value = f"{filename_folder_prefix}/{auto_tt_rec_filename_cmd_value}"
                        config[auto_tt_rec_filename_cmd] = auto_tt_rec_filename_cmd_value

            config["iso-filename"] = str(iso_dirpath / region_filename_and_name.filename)
            config["output-video-filename"] = f"{filename_folder_prefix}/test_vids/{datetime_now_str}_{output_video_filepath_stem}_{region_filename_and_name.name}.{output_video_filepath_extension}"

            extra_gecko_codes_filename = config.get("extra-gecko-codes-filename")
            if extra_gecko_codes_filename is not None:
                if not extra_gecko_codes_filename.endswith("malformed_gecko_codes.ini") and not extra_gecko_codes_filename.endswith("colliding_gecko_codes.ini"):
                    extra_gecko_codes_filepath = pathlib.Path(extra_gecko_codes_filename)
                    extra_gecko_codes_filename = f"{extra_gecko_codes_filepath.with_suffix('')}_{region_filename_and_name.name}{extra_gecko_codes_filepath.suffix}"

                config["extra-gecko-codes-filename"] = f"{filename_folder_prefix}/{extra_gecko_codes_filename}"

            top_10_gecko_code_filename = config.get("top-10-gecko-code-filename")
            if top_10_gecko_code_filename is not None:
                top_10_gecko_code_filepath = pathlib.Path(top_10_gecko_code_filename)
                top_10_gecko_code_basename = top_10_gecko_code_filepath.name

                if top_10_gecko_code_basename == "wrong_region.txt":
                    wrong_region_name = random.choice(region_names_except_selected[region_filename_and_name.name])
                    top_10_gecko_code_parent_filepath = top_10_gecko_code_filepath.parent
                    top_10_gecko_code_filename = str(top_10_gecko_code_parent_filepath / f"gba_bc3_tops_{wrong_region_name}.txt")
                elif top_10_gecko_code_basename == "gba_bc3_tops.txt":
                    top_10_gecko_code_filename = f"{top_10_gecko_code_filepath.with_suffix('')}_{region_filename_and_name.name}{top_10_gecko_code_filepath.suffix}"

                config["top-10-gecko-code-filename"] = f"{filename_folder_prefix}/{top_10_gecko_code_filename}"

            debug_manual_auto_add = config.get("debug-manual-auto-add")
            if debug_manual_auto_add is not None:
                config["debug-manual-auto-add"] = f"{filename_folder_prefix}/{debug_manual_auto_add}"

            if not options["do-not-randomize-folders"] and debug_manual_auto_add is None:
                for cmd_folders in all_cmd_folders:
                    if cmd_folders.name == "extra-hq-textures-folder" and config.get("extra-hq-textures-folder") == "this_does_not_exist":
                        continue
    
                    cmd_folder = random.choice(cmd_folders.folders)
                    if cmd_folder.is_default:
                        resulting_cmd_folder_name = None
                        print(f"Chose default {cmd_folders.name} folder!")
                    else:
                        resulting_cmd_folder_name = cmd_folder.name
                        print(f"Chose {cmd_folders.name} \"{cmd_folder.name}\"!")
                        if cmd_folder.is_relative:
                            if random.randint(0, 1) == 0:
                                relative_folder_additive = random.choice(relative_folder_additives)
                                print(f"Added relative folder additive \"{relative_folder_additive}\"!")
                                resulting_cmd_folder_name = f"{relative_folder_additive}/{resulting_cmd_folder_name}"
    
                            resulting_cmd_folder_name = f"{filename_folder_prefix}/{resulting_cmd_folder_name}"

                    config[cmd_folders.name] = resulting_cmd_folder_name

            storage_folder = config.get("storage-folder")
            if storage_folder is None:
                storage_folder = f"{release_auto_tt_rec_directory}/storage"

            auto_add_dirname = f"{storage_folder}/auto-add"

            ignore_auto_add_missing_files = config.get("ignore-auto-add-missing-files")

            if test_release:
                release_auto_tt_rec_dirpath = pathlib.Path(release_auto_tt_rec_directory)

                if release_auto_tt_rec_dirpath.is_dir():
                    if release_clean_install == RELEASE_CLEAN_INSTALL_YES:
                        clean_release = True
                    elif release_clean_install == RELEASE_CLEAN_INSTALL_RANDOM:
                        clean_release = random.randint(0, 1) == 0
                    elif release_clean_install == RELEASE_CLEAN_INSTALL_NO:
                        clean_release = False
                    else:
                        raise RuntimeError()

                    if first_run or clean_release:
                        first_run = False
                        shutil.rmtree(release_auto_tt_rec_dirpath)
                        extract_release = True
                    else:
                        extract_release = False
                else:
                    extract_release = True

                if extract_release:
                    subprocess.run((sevenz_filename, "x", release_auto_tt_rec_7z_filename, "-orelease_working/*"), check=True)
                    shutil.copy2("test_data/record_ghost_for_release_test.bat", f"{release_auto_tt_rec_directory}/record_ghost.bat")

                temp_config_filename = f"{release_auto_tt_rec_directory}/config.yml"
            else:
                temp_config_filename = f"temp/{config_basename}"
                pathlib.Path("temp").mkdir(exist_ok=True, parents=True)

            if on_wsl:
                ffmpeg_name = "ffmpeg"
                ffprobe_name = "ffprobe"
            else:
                ffmpeg_name = "bin/ffmpeg.exe"
                ffprobe_name = "bin/ffprobe.exe"

            config["ffmpeg-filename"] = ffmpeg_name
            config["ffprobe-filename"] = ffprobe_name

            with open(temp_config_filename, "w+") as f:
                yaml.dump(config, f)

            if test_release:
                saved_cwd = os.getcwd()
                os.chdir(release_auto_tt_rec_directory)
                completed_process = subprocess.run((".\\record_ghost.bat",))
                os.chdir(saved_cwd)
            else:
                completed_process = subprocess.run((python_filename, "record_ghost.py", "-cfg", temp_config_filename))

            if completed_process.returncode == 0:
                cur_test_result_output = f"SUCCESS: region {region_filename_and_name.name}, config {config_basename}"
            else:
                auto_add_dirpath = pathlib.Path(auto_add_dirname)
                auto_add_dirpath_exists = auto_add_dirpath.is_dir()

                cur_test_result_output = f"FAILURE: region {region_filename_and_name.name}, config {config_basename}, code: {completed_process.returncode}, auto-add {auto_add_dirname} exists: {auto_add_dirpath_exists}"
                amanita_abyss_autogenerated_szs_filename = f"{storage_folder}/szs/3A2DCD337343E86EA688AE27BB409F892EFC5AAC.szs"
                amanita_abyss_autogenerated_szs_filepath = pathlib.Path(amanita_abyss_autogenerated_szs_filename)

                if ignore_auto_add_missing_files == "true":
                    cur_test_result_output += f", autogenerated SZS {amanita_abyss_autogenerated_szs_filename} exists: {amanita_abyss_autogenerated_szs_filepath.is_file()}"

            cur_test_result_output = f"\n===============================================\n{cur_test_result_output}\n===============================================\n\n\n\n\n"
            print(cur_test_result_output)

    with open("test_results.dump", "w+") as f:
        f.write(test_result_output)

if __name__ == "__main__":
    main()
