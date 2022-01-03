import pathlib
import identifiers
import shutil
import os

from stateclasses.speedometer import *

def make_empty_nand_course_dir():
    dolphin_nand_course_dir_filepath = pathlib.Path(f"dolphin/User/Wii/RMCX01/Race/Course")
    dolphin_nand_course_dir_filepath.mkdir(parents=True, exist_ok=True)
    with os.scandir(dolphin_nand_course_dir_filepath) as entries:
        for dir_entry in entries:
            if dir_entry.is_file():
                os.unlink(dir_entry.path)
            else:
                raise RuntimeError(f"Directory {dir_entry} found in NAND Course folder!")

def replace_track(szs_filename, rkg):
    make_empty_nand_course_dir()
    if szs_filename is None:
        return

    szs_filepath = pathlib.Path(szs_filename)
    track_filename = identifiers.track_filenames[rkg.track_by_human_id]
    dolphin_nand_course_filepath = pathlib.Path(f"dolphin/User/Wii/RMCX01/Race/Course/{track_filename}")
    shutil.copy(szs_filepath, dolphin_nand_course_filepath)

def add_fancy_km_h_race_szs_if_necessary(speedometer):
    dolphin_nand_scene_ui_dirpath = pathlib.Path(f"dolphin/User/Wii/RMCX01/Scene/UI")
    dolphin_nand_scene_ui_dirpath.mkdir(parents=True, exist_ok=True)
    # todo localize this
    dolphin_nand_race_szs_filepath = pathlib.Path(f"dolphin/User/Wii/RMCX01/Scene/UI/Race_U.szs")

    if speedometer.style == SOM_FANCY_KM_H:
        shutil.copy("data/Race_U.szs", dolphin_nand_race_szs_filepath)
    else:
        dolphin_nand_race_szs_filepath.unlink(missing_ok=True)
