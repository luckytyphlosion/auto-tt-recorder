import platform
on_wsl = "microsoft" in platform.uname()[3].lower()

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

    os.chdir("dolphin/")

    if on_wsl:
        run_dolphin_wsl(iso_filename, hide_window)
    else:
        run_dolphin_non_wsl(iso_filename, hide_window)

    os.chdir("..")

def run_dolphin_non_wsl(iso_filename, hide_window):
    args = ["./DolphinR.exe", "-b", "-e", iso_filename]
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

def run_dolphin_wsl(iso_filename, hide_window)
    # this will complete almost immediately
    args = ["powershell.exe", "-NoProfile", "-Command", "(", "Start-Process", "-PassThru", "-FilePath", "dolphin\\DolphinR.exe", "-ArgumentList"]
    if hide_window:
        args.extend(('"-hm"', ",", '"-dr"', ","))

    args.extend(('"-b"', ",", fr"""'-e "{iso_filename}"'""", ").id > dolphin_pid.log"))

    # need to use utf-8 encoding to prevent WSL from changing fonts
    # https://github.com/microsoft/WSL/issues/3988#issuecomment-706667720
    subprocess.run(args, encoding="utf-8")

    with open("dolphin_pid.log", "r", encoding="utf-16") as f:
        dolphin_pid = f.read().strip()

    try:
        int(dolphin_pid)
    except ValueError as e:
        raise RuntimeError(f"Non-integer dolphin PID \"{dolphin_pid}\"!") from e

    while True:
        process_result = subprocess.run(("powershell.exe", "-NoProfile", "-Command", "Wait-Process", "-Id", dolphin_pid, "-Timeout", "30", "2>&1>$null"))
        if process_result.returncode == 0:
            break

        # some abnormal condition, implement later
        if False:
            subprocess.run(("taskkill.exe", "/f", "/pid", dolphin_pid))
            break
