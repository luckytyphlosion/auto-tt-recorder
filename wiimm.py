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

import platform
import subprocess

wit_filename = None
wszst_filename = None
wkmpt_filename = None

def get_wit_wszst_filename():
    global wit_filename
    global wszst_filename

    if wit_filename is None and wszst_filename is None:
        platform_system_lower = platform.system().lower()
        if platform_system_lower == "linux":
            wit_filename = "bin/wiimm/linux/wit"
            wszst_filename = "bin/wiimm/linux/wszst"
        elif platform_system_lower == "windows":
            wit_filename = "bin/wiimm/cygwin64/wit.exe"
            wszst_filename = "bin/wiimm/cygwin64/wszst.exe"
        else:
            raise RuntimeError(f"Unsupported operating system {platform.system()}!")

    return wit_filename, wszst_filename

def get_wkmpt_filename():
    global wkmpt_filename

    if wkmpt_filename is None:
        platform_system_lower = platform.system().lower()
        if platform_system_lower == "linux":
            wkmpt_filename = "bin/wiimm/linux/wkmpt"
        elif platform_system_lower == "windows":
            wkmpt_filename = "bin/wiimm/cygwin64/wkmpt.exe"
        else:
            raise RuntimeError(f"Unsupported operating system {platform.system()}!")

    return wkmpt_filename

def check_track_has_speedmod(track_filename):
    wkmpt_filename = get_wkmpt_filename()

    wkmpt_output = subprocess.check_output((wkmpt_filename, "STGI", "-H", track_filename), encoding="utf-8")
    #print(f"wkmpt_output: {wkmpt_output}")
    stgi_info, track_filename_from_wkmpt = wkmpt_output.strip().split(" : ", maxsplit=1)
    split_stgi_info = stgi_info.split()
    return split_stgi_info[2] != "--" and split_stgi_info[2] != "1.00"
