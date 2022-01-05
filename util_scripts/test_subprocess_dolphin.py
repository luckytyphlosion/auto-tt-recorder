import subprocess
import time
import pathlib

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

if __name__ == "__main__":
    main()
    #main2()

