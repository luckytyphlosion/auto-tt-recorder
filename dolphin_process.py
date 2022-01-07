import platform
import sys
import pathlib
import subprocess
import os
import glob
import re
import random
import time

on_wsl = "microsoft" in platform.uname()[3].lower()
good_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-/.\\")
dolphin_filename_regex = re.compile(r"Dolphin_[0-9]+_[0-9]+.exe")

def sanitize_and_check_iso_exists(iso_filename):
    # bug in Dolphin Lua Core will cause Dolphin's memory and disk usage to spike extremely
    # if the filename ends with spaces
    iso_filename = iso_filename.strip()

    if not all(c in good_chars for c in iso_filename):
        raise RuntimeError("Found illegal characters in ISO path to file (safeguard against shell injection)!")

    iso_filepath = pathlib.Path(iso_filename)
    if not iso_filepath.exists():
        raise RuntimeError(f"Iso filename \"{iso_filename}\" does not exist!")

    return iso_filename

# IMPORTANT! ISO filename MUST be sanitized
# Most notably, a bug in Dolphin-Lua-Core will cause Dolphin to spike in memory and disk usage
# if the passed ISO filename ends in a space
# Also, if on WSL, ISO filename must also be sanitized to prevent shell injection within powershell.exe
def run_dolphin(iso_filename, hide_window, sanitize_iso_filename=True):
    iso_filename = sanitize_and_check_iso_exists(iso_filename)
    double_dot_iso_filename = str(".." / pathlib.Path(iso_filename))

    os.chdir("dolphin/")

    if on_wsl:
        run_dolphin_wsl(double_dot_iso_filename, hide_window)
    else:
        run_dolphin_non_wsl(double_dot_iso_filename, hide_window)

    os.chdir("..")

def run_dolphin_non_wsl(double_dot_iso_filename, hide_window):
    args = ["./DolphinR.exe", "-b", "-e", double_dot_iso_filename]
    if hide_window:
        args.extend(("-hm", "-dr"))

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
def run_dolphin_wsl(double_dot_iso_filename, hide_window):
    good_dolphin_filenames = [name for name in glob.iglob("Dolphin*.exe") if name in ("Dolphin.exe", "DolphinR.exe") or dolphin_filename_regex.match(name)]

    if len(good_dolphin_filenames) != 1:
        raise RuntimeError("Multiple different Dolphin executables in dolphin/!")

    dolphin_filename = good_dolphin_filenames[0]
    dolphin_filepath = pathlib.Path(dolphin_filename)
    new_dolphin_filename = f"Dolphin_{int(time.time())}_{random.randint(0, 65535)}.exe"
    new_dolphin_filepath = pathlib.Path(new_dolphin_filename)
    dolphin_filepath.rename(new_dolphin_filepath)

    args = [f"./{new_dolphin_filename}", "-b", "-e", double_dot_iso_filename]
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
