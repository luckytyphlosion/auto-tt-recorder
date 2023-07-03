# Copyright (C) 2022 luckytyphlosion
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import pathlib
import identifiers
import shutil
import os
import dir_config

from stateclasses.speedometer import *

def make_empty_nand_course_dir():
    dolphin_nand_course_dir_filepath = pathlib.Path(f"{dir_config.dolphin_dirname}/User/Wii/RMCX01/Race/Course")
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
    dolphin_nand_course_filepath = pathlib.Path(f"{dir_config.dolphin_dirname}/User/Wii/RMCX01/Race/Course/{track_filename}")
    shutil.copy(szs_filepath, dolphin_nand_course_filepath)

def add_fancy_km_h_race_szs_if_necessary(speedometer, region):
    dolphin_nand_scene_ui_dirpath = pathlib.Path(f"{dir_config.dolphin_dirname}/User/Wii/RMCX01/Scene/UI")
    dolphin_nand_scene_ui_dirpath.mkdir(parents=True, exist_ok=True)
    # todo localize this
    dolphin_nand_race_szs_filepath = pathlib.Path(f"{dir_config.dolphin_dirname}/User/Wii/RMCX01/Scene/UI/Race_{region.default_language_suffix}.szs")

    if speedometer.style == SOM_FANCY_KM_H:
        shutil.copy("data/Race_U.szs", dolphin_nand_race_szs_filepath)
    else:
        dolphin_nand_race_szs_filepath.unlink(missing_ok=True)

extended_region_src_files_by_region = {
    "PAL": (
        "Channel.szs", "MenuSingle.szs"
    ),
    "NTSC-U": (
        "Channel.szs", "MenuSingle.szs"
    ),
    "NTSC-J": (
        "Channel.szs", "MenuSingle.szs"
    ),
    "NTSC-K": (
        "Channel_R.szs", "MenuSingle_R.szs"
    )
}

def add_extended_region_files(region):
    dolphin_nand_scene_ui_dirpath = pathlib.Path(f"{dir_config.dolphin_dirname}/User/Wii/RMCX01/Scene/UI")
    dolphin_nand_scene_ui_dirpath.mkdir(parents=True, exist_ok=True)

    extended_region_src_files = extended_region_src_files_by_region[region.name]
    for extended_region_src_file in extended_region_src_files:
        extended_region_src_filepath = pathlib.Path(f"data/extended_regions/{extended_region_src_file}")
        extended_region_dest_filepath = pathlib.Path(f"{dir_config.dolphin_dirname}/User/Wii/RMCX01/Scene/UI/{extended_region_src_file}")

        if not extended_region_dest_filepath.is_file():
            shutil.copy(extended_region_src_filepath, extended_region_dest_filepath)

hq_textures_src_filenames = (
    "data/tex1_64x64_8b7aa8aaa750b196_5.png",
    "data/tex1_64x64_a23e5f789681e0b3_5.png",
    "data/tex1_64x64_9f365352984ccbe6_5.png",
    "data/tex1_64x64_54f9b0512c515f6e_5.png",
    "data/tex1_64x64_48711ec1fc700501_5.png",
    "data/tex1_64x64_475472d0a71a5ddb_5.png"
)

# not technically mkw filesys
def copy_hq_textures_if_necessary(hq_textures, region, extra_hq_textures_src_folder):
    if not hq_textures:
        return

    dolphin_hq_textures_dest_dir = pathlib.Path(f"{dir_config.dolphin_dirname}/User/Load/Textures/{region.title_id}")
    dolphin_hq_textures_dest_dir.mkdir(parents=True, exist_ok=True)

    for hq_texture_src_filename in hq_textures_src_filenames:
        hq_texture_src_filepath = pathlib.Path(hq_texture_src_filename)
        hq_texture_dest_filepath = pathlib.Path(f"{dir_config.dolphin_dirname}/User/Load/Textures/{region.title_id}/{hq_texture_src_filepath.name}")

        if not hq_texture_dest_filepath.is_file():
            shutil.copy(hq_texture_src_filepath, hq_texture_dest_filepath)

    extra_textures_filepath = pathlib.Path(f"{dir_config.dolphin_dirname}/User/Load/Textures/{region.title_id}/extra_textures")
    extra_textures_filepath.mkdir(parents=True, exist_ok=True)

    if extra_hq_textures_src_folder is None:
        extra_textures_root, extra_textures_dirs, extra_textures_files = next(os.walk(extra_textures_filepath))
        for extra_textures_dir in extra_textures_dirs:
            shutil.rmtree(os.path.join(extra_textures_root, extra_textures_dir))
    
        for extra_textures_file in extra_textures_files:
            os.unlink(os.path.join(extra_textures_root, extra_textures_file))
    else:
        extra_hq_textures_src_dirpath = pathlib.Path(extra_hq_textures_src_folder)
        if not extra_hq_textures_src_dirpath.is_dir():
            raise RuntimeError(f"Extra hq textures folder \"{extra_hq_textures_src_folder}\" does not exist!")

        extra_textures_dest_dirpath = extra_textures_filepath

        all_extra_textures_src_files_relative = set()
        all_extra_textures_dest_files_relative = set()

        print(f"Copying over HQ Textures!")

        saved_cur_directory = os.getcwd()
        os.chdir(extra_hq_textures_src_dirpath)

        for extra_textures_src_root, extra_textures_src_dirs, extra_textures_src_files in os.walk("."):
            all_extra_textures_src_files_relative.update(os.path.join(extra_textures_src_root, extra_textures_src_file) for extra_textures_src_file in extra_textures_src_files)

        os.chdir(saved_cur_directory)
        os.chdir(extra_textures_dest_dirpath)
        for extra_textures_dest_root, extra_textures_dest_dirs, extra_textures_dest_files in os.walk("."):
            all_extra_textures_dest_files_relative.update(os.path.join(extra_textures_dest_root, extra_textures_dest_file) for extra_textures_dest_file in extra_textures_dest_files)

        os.chdir(saved_cur_directory)

        for extra_textures_src_file_relative in all_extra_textures_src_files_relative:
            extra_textures_src_filepath = extra_hq_textures_src_dirpath / pathlib.Path(extra_textures_src_file_relative)
            extra_textures_dest_filepath = extra_textures_dest_dirpath / pathlib.Path(extra_textures_src_file_relative)
            file_changed = False

            if extra_textures_src_file_relative not in all_extra_textures_dest_files_relative:
                file_changed = True
                extra_textures_dest_filepath.parent.mkdir(parents=True, exist_ok=True)
            elif extra_textures_src_filepath.stat().st_mtime != extra_textures_dest_filepath.stat().st_mtime:
                file_changed = True

            if file_changed:
                #print(f"extra_textures_src_filepath: {extra_textures_src_filepath}, extra_textures_dest_filepath: {extra_textures_dest_filepath}")
                shutil.copy2(extra_textures_src_filepath, extra_textures_dest_filepath)

        for extra_textures_dest_file_relative in all_extra_textures_dest_files_relative:
            if extra_textures_dest_file_relative not in all_extra_textures_src_files_relative:
                extra_textures_dest_filepath = extra_textures_dest_dirpath / pathlib.Path(extra_textures_dest_file_relative)
                #print(f"extra_textures_dest_filepath remove: {extra_textures_dest_filepath}")
                os.unlink(extra_textures_dest_filepath)

        #shutil.copytree(extra_hq_textures_src_dirpath, extra_textures_dest_filepath)
