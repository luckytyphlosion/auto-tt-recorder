import subprocess
import time
import pathlib
import os
import signal
import glob
import re
import random

dolphin_filename_regex = re.compile(r"Dolphin_[0-9]+_[0-9]+.exe")

def keep_only_safe_chars(s):
    return "".join([c for c in s if c in good_chars])

good_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-/.\\")

def main2():
    iso_filename = "../../RMCE 01/RMCE01.iso"
    subprocess.run(("powershell.exe", "-Command", "(", "Start-Process", "-PassThru", "-FilePath", "dolphin\\DolphinR.exe", "-ArgumentList", '"-b"', ",", fr"""'-e "{iso_filename}"'""", ").id > dolphin_pid.log"), encoding="utf-8")
    #print(f"output: {output}")

def main():
    iso_filename = "../../RMCE 01/RMCE01.iso"
    #popen = subprocess.Popen(("powershell.exe", "-Command", "$dolphin_pid = (", "Start-Process", "-NoNewWindow", "-PassThru", "-FilePath", "dolphin\\DolphinR.exe", "-ArgumentList", '"-b"', ",", fr"""'-e "{iso_filename}"'""", ").id ; $dolphin_pid > dolphin_pid.log ; Wait-Process -Id $dolphin_pid"), encoding="utf-8")
    #popen.terminate()
    #subprocess.run(("powershell.exe", "-Command", "$dolphin_pid = (", "Start-Process", "-PassThru", "-FilePath", "dolphin\\DolphinR.exe", "-ArgumentList", '"-b"', ",", fr"""'-e "{iso_filename}"'""", ").id ; $dolphin_pid > dolphin_pid.log ; Wait-Process -Id $dolphin_pid"), encoding="utf-8")

#powershell.exe -Command \$did = "(" Start-Process -PassThru -FilePath "dolphin/DolphinR.exe" -ArgumentList \"-b\",\'-e \"../../RMCE 01/RMCE01.iso\"\' ").id" \; \$did > dolphin_pid.log \; Wait-Process -Id \$did

    #popen = subprocess.Popen(
    #    fr"""powershell.exe -Command "(" Start-Process -NoNewWindow -PassThru -FilePath dolphin\\DolphinR.exe -ArgumentList \"-b\",\'-e \"'{iso_filename}'\"\' ").id" """, shell=True, encoding="utf-8")

    subprocess.run(("powershell.exe", "-NoProfile", "-Command", "(", "Start-Process", "-PassThru", "-FilePath", "dolphin\\DolphinR.exe", "-ArgumentList", '"-b"', ",", fr"""'-e "{iso_filename}"'""", ").id > dolphin_pid.log"), encoding="utf-8")
    #return
    # args.extend(('"-b"', ",", fr"""'-e "{iso_filename}"'""", ").id ; $dolphin_pid > dolphin_pid.log ; Wait-Process -Id $dolphin_pid"))

    #popen = subprocess.Popen(("cmd.exe", "/c", "start", "/wait", "powershell.exe", "-Command", "$dolphin_pid = (", "Start-Process", "-NoNewWindow", "-PassThru", "-FilePath", "dolphin\\DolphinR.exe", "-ArgumentList", '"-b"', ",", fr"""'-e "{iso_filename}"'""", ").id ; $dolphin_pid > dolphin_pid.log ; Wait-Process -Id $dolphin_pid"), encoding="utf-8")

    with open("dolphin_pid.log", "r", encoding="utf-16") as f:
        dolphin_pid = f.read().strip()

    try:
        int(dolphin_pid)
    except ValueError as e:
        raise RuntimeError(f"Non-integer dolphin PID \"{dolphin_pid}\"!") from e

    kill_path = pathlib.Path("kill.txt")

    #while True:
    #    returncode = popen.poll()
    #    # dolphin exited normally
    #    if returncode is not None:
    #        break
    #
    #    # some abnormal condition, implement later
    #    if kill_path.is_file():
    #        popen.terminate()
    #        # wsl memes
    #        #subprocess.run(("taskkill.exe", "/f", "/im", "DolphinR.exe"))
    #        break
    #
    #    time.sleep(1)

    while True:
        process_result = subprocess.run(("powershell.exe", "-NoProfile", "-Command", "Wait-Process", "-Id", dolphin_pid, "-Timeout", "3", "2>&1>$null"))
        if process_result.returncode == 0:
            break

        if kill_path.is_file():
            subprocess.run(("taskkill.exe", "/f", "/pid", dolphin_pid))
            break

        #returncode = popen.poll()
        ## dolphin exited normally
        #if returncode is not None:
        #    break
        #
        #    #raise RuntimeError()
        #
        #    # some abnormal condition, implement later
        #    if kill_path.is_file():
        #        popen.terminate()
        #        ## wsl memes
        #        #subprocess.run(("taskkill.exe", "/f", "/im", "DolphinR.exe"))
        #        break
        #
        #    time.sleep(1)
    #except Exception as e:
    #    #time.sleep(1)
    #    popen.terminate()
    #    #time.sleep(1)
    #    raise e

    #try:
    #    popen_out, popen_err = popen.communicate(timeout=10)
    #    print(f"popen_out: {popen_out}, popen_err: {popen_err}")
    #except subprocess.TimeoutExpired:
    #    pass
    #
    #while True:
    #    returncode = popen.poll()
    #    if returncode is not None:
    #        print(f"returncode: {returncode}")
    #        break
    #    time.sleep(1)

    #try:
    #    with open("dolphin_pid.log", "r", encoding="utf_16_le") as f:
    #        dolphin_pid = f.read().strip()
    #
    #    while True:
    #        returncode = popen.poll()
    #        # dolphin exited normally
    #        if returncode is not None:
    #            break
    #
    #        # some abnormal condition, implement later
    #        if False:
    #            popen.terminate()
    #            # wsl memes
    #            subprocess.run(("taskkill.exe", "/f", "/im", "DolphinR.exe"))
    #            break
    #    
    #        time.sleep(1)
    #except Exception as e:
    #    popen.terminate()
    #    raise e

    #print(f"result: {result}")

def kill_process_through_taskkill(popen, pid):
    subprocess.run(("taskkill.exe", "/f", "/pid", dolphin_pid))
    time.sleep(0.1)
    process_killed = False

    for i in range(5):
        returncode = popen.poll()
        if returncode is not None:
            process_killed = True
            break

        time.sleep(1)

    if not process_killed:
        raise RuntimeError("FATAL ERROR: powershell.exe process stuck, WSL console will now corrupt.")

def run_dolphin_wsl(iso_filename, hide_window):
    double_dot_iso_filename = str(".." / pathlib.Path(iso_filename))
    args = ["powershell.exe", "-NoProfile", "-Command", "(", "Start-Process", "-PassThru", "-FilePath", "DolphinR.exe", "-ArgumentList"]

    #args = ["powershell.exe", "-NoProfile", "-Command", "$dolphin_pid = (", "Start-Process", "-PassThru", "-FilePath", "DolphinR.exe", "-ArgumentList"]
    if hide_window:
        args.extend(('"-hm"', ",", '"-dr"', ","))

    args.extend(('"-b"', ",", fr"""'-e "{double_dot_iso_filename}"'""", ").id > dolphin_pid.log"))
    subprocess.run(args, encoding="utf-8")

    with open("dolphin_pid.log", "r", encoding="utf-16") as f:
        dolphin_pid = f.read().strip()

    try:
        int(dolphin_pid)
    except ValueError as e:
        raise RuntimeError(f"Non-integer dolphin PID \"{dolphin_pid}\"!") from e

    #args.extend(('"-b"', ",", fr"""'-e "{double_dot_iso_filename}"'""", ").id ; $dolphin_pid > dolphin_pid.log ; Wait-Process -Id $dolphin_pid"))

    kill_path = pathlib.Path("kill.txt")

    # need to use utf-8 encoding to prevent WSL from changing fonts
    # https://github.com/microsoft/WSL/issues/3988#issuecomment-706667720

    #subprocess.run(("powershell.exe", "-NoProfile", "-Command", "Wait-Process", "-Id", dolphin_pid, "-Timeout", "30", "2>&1>$null"))

    def exit_script(sig, frame):
        print('You pressed Ctrl+C!')
        kill_process_through_taskkill(popen, dolphin_pid)
        sys.exit(0)

    original_sigint_handler = signal.getsignal(signal.SIGINT)

    signal.signal(signal.SIGINT, exit_script)

    try:
        popen = subprocess.Popen(("powershell.exe", "-NoProfile", "-Command", "Wait-Process", "-Id", dolphin_pid), encoding="utf-8")

        while True:
            print("hello")
            returncode = popen.poll()
            # dolphin exited normally
            if returncode is not None:
                break

            # some abnormal condition, implement later
            if kill_path.is_file():
                kill_process_through_taskkill(popen, dolphin_pid)
                break

            time.sleep(1)
    except KeyboardInterrupt as e:
        print("hello")
        if popen is not None:
            kill_process_through_taskkill(popen, dolphin_pid)

        sys.exit(e)

    signal.signal(signal.SIGINT, original_sigint_handler)

def run_dolphin_wsl2(iso_filename, hide_window):
    double_dot_iso_filename = str(".." / pathlib.Path(iso_filename))

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

    kill_path = pathlib.Path("kill.txt")

    try:
        popen = subprocess.Popen(args)
    
        while True:
            returncode = popen.poll()
            # dolphin exited normally
            if returncode is not None:
                break
    
            # some abnormal condition, implement later
            if kill_path.is_file():
                popen.terminate()
                subprocess.run(("taskkill.exe", "/f", "/im", new_dolphin_filename))
                break

            time.sleep(1)

    except KeyboardInterrupt as e:
        popen.terminate()
        subprocess.run(("taskkill.exe", "/f", "/im", new_dolphin_filename))
        raise RuntimeError(e)

def main3():
    os.chdir("../dolphin")

    run_dolphin_wsl2("../../RMCE 01/RMCE01.iso", False)

    os.chdir("../util_scripts")

if __name__ == "__main__":
    main3()
    #main2()

