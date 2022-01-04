import platform
on_wsl = "microsoft" in platform.uname()[3].lower()

def run_dolphin(hide_window):
    os.chdir("dolphin/")
    args = ["powershell.exe", "-Command", "(", "Start-Process", "-NoNewWindow", "-FilePath""./DolphinR.exe", "-b", "-e", iso_filename]
    if hide_window:
        args.extend(("-hm", "-dr"))

    subprocess.run(args, check=True)
    #popen = subprocess.Popen(args)
    #popen = subprocess.Popen(("./DolphinR.exe", "-b", "-e", iso_filename))
    #kill_path = pathlib.Path("kill.txt")
    #while True:
    #    if kill_path.is_file():
    #        popen.terminate()
    #        # wsl memes
    #        subprocess.run(("taskkill.exe", "/f", "/im", "DolphinR.exe"))
    #        break
    #
    #    time.sleep(1)

    os.chdir("..")
    