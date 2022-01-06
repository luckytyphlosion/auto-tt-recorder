import subprocess
import time

def main():

    try:
        popen = subprocess.Popen(("../dolphin/DolphinR.exe"), encoding="utf-8")

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
        raise RuntimeError(e)

if __name__ == "__main__":
    main()
