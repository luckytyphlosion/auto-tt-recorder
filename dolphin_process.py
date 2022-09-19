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
import sys
import pathlib
import subprocess
import os
import glob
import re
import random
import time

import job_process

on_wsl = "microsoft" in platform.uname()[3].lower()
dolphin_filename_regex = re.compile(r"Dolphin_[0-9]+_[0-9]+.exe")

# IMPORTANT! ISO filename MUST be sanitized
# Most notably, a bug in Dolphin-Lua-Core will cause Dolphin to spike in memory and disk usage
# if the passed ISO filename ends in a space
# Also, if on WSL, ISO filename must also be sanitized to prevent shell injection within powershell.exe
def run_dolphin(mkw_iso, hide_window, sanitize_iso_filename=True):
    iso_filename_resolved = str(pathlib.Path(mkw_iso.iso_filename).resolve())

    dolphin_status_path = pathlib.Path("dolphin/status.txt")
    dolphin_status_path.unlink(missing_ok=True)

    os.chdir("dolphin/")

    if on_wsl:
        run_dolphin_wsl(iso_filename_resolved, hide_window)
    elif platform.system() == "Windows":
        run_dolphin_windows(iso_filename_resolved, hide_window)
    else:
        run_dolphin_generic(iso_filename_resolved, hide_window)

    os.chdir("..")

    if not dolphin_status_path.is_file():
        raise RuntimeError("User terminated Dolphin before completion!")

    with open(dolphin_status_path, "r") as f:
        dolphin_status = f.read()

    if dolphin_status.strip() != "":
        raise RuntimeError(f"Error occurred while running Dolphin: {dolphin_status}")

# https://docs.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getexitcodeprocess?redirectedfrom=MSDN
STILL_ACTIVE = 259

# Taken from https://stackoverflow.com/questions/1230669/subprocess-deleting-child-processes-in-windows/12942797#12942797
def run_dolphin_windows(iso_filename_resolved, hide_window):
    dolphin_command = ["./Dolphin.exe", "-b", "-e", iso_filename_resolved]
    if hide_window:
        dolphin_command.extend(("-hm", "-dr"))

    job_process.run_subprocess_as_job(dolphin_command)

def run_dolphin_generic(iso_filename_resolved, hide_window):
    args = ["./Dolphin.exe", "-b", "-e", iso_filename_resolved]
    if hide_window:
        args.extend(("-hm", "-dr"))

    try:
        popen = subprocess.Popen(args)

        while True:
            returncode = popen.poll()
            # dolphin exited normally
            if returncode is not None:
                break

            # some abnormal condition, implement later
            if False:
                popen.terminate()
                break

            time.sleep(1)

    except KeyboardInterrupt as e:
        popen.terminate()
        #subprocess.run(("taskkill.exe", "/f", "/im", new_dolphin_filename))
        raise RuntimeError(e)

# dumbest hack ever
# goal: run Dolphin through WSL while maintaining the following goals
# - there should be a way to determine when this specific Dolphin instance stops
# - We should be able to kill dolphin python-side if something goes wrong (e.g. dolphin's lua freezes)
#   - We cannot kill dolphin using python's subprocess interface because we're running Linux python and Dolphin is a windows application
#   - the old solution was to use a custom dolphin filename and execute taskkill.exe, passing the custom dolphin filename as the image name
#   - However, this still has a possibility of creating conflicts if multiple DolphinR.exes are being run
#   - using a randomized "unique" name is undesirable as other OSes won't need to rename Dolphin.exe, leading to an asymmetry
#   - instead, the solution is to run Dolphin via the powershell, so we get access to the correct PID which we can use to kill
#   - the original powershell.exe command would exit immediately after fetching dolphin's PID while running in the background
#   - however, there may be an extreme situation where dolphin dies but another process uses the PID which it just released (is this even possible)
#   - so to make sure that we only kill dolphin's PID, we use Popen and have the powershell.exe command wait for the dolphin it just started to die
#   - this is a poor explanation but whatever
#   - actually, couldn't do the above
#   - terminating powershell.exe via popen.terminate() will corrupt the wsl console
#   - https://github.com/microsoft/WSL/issues/7367
#   - so just fallback to original behaviour

# nothing worked, powershell.exe through wsl has issues, so fallback to the renaming solution
def run_dolphin_wsl(iso_filename_resolved, hide_window):
    windows_iso_filename_resolved = subprocess.check_output(("wslpath", "-w", str(iso_filename_resolved)), encoding="utf-8").replace("\n", "")

    good_dolphin_filenames = [name for name in glob.iglob("Dolphin*.exe") if name in ("Dolphin.exe", "DolphinR.exe") or dolphin_filename_regex.match(name)]

    if len(good_dolphin_filenames) != 1:
        raise RuntimeError("Multiple different Dolphin executables in dolphin/!")

    dolphin_filename = good_dolphin_filenames[0]
    dolphin_filepath = pathlib.Path(dolphin_filename)
    new_dolphin_filename = f"Dolphin_{int(time.time())}_{random.randint(0, 65535)}.exe"
    new_dolphin_filepath = pathlib.Path(new_dolphin_filename)
    dolphin_filepath.rename(new_dolphin_filepath)

    args = [f"./{new_dolphin_filename}", "-b", "-e", windows_iso_filename_resolved]
    if hide_window:
        args.extend(("-hm", "-dr"))

    try:
        popen = subprocess.Popen(args)
    
        while True:
            returncode = popen.poll()
            # dolphin exited normally
            if returncode is not None:
                break
    
            # some abnormal condition, implement later
            if False:
                popen.terminate()
                subprocess.run(("taskkill.exe", "/f", "/im", new_dolphin_filename))
                break

            time.sleep(1)

    except KeyboardInterrupt as e:
        popen.terminate()
        subprocess.run(("taskkill.exe", "/f", "/im", new_dolphin_filename))
        raise RuntimeError(e)
