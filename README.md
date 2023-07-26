# auto-tt-recorder
**[Discord link (get updated on new releases here)](https://discord.gg/6FqfpnqP57)**

Automatically records time trials in Mario Kart Wii.

# Download
**Download the latest release [here](https://github.com/luckytyphlosion/auto-tt-recorder/releases/latest)**. You can choose either the 7z release or zip release, but the 7z release needs 7-Zip (or WinRAR, but don't use this) installed.

# Help
Blounard (blounard on Discord) has created a tutorial which can be found [here](https://www.youtube.com/watch?v=Otuem1H9Yrg).

Documentation for each command can be found [here](docs/DOCS.md).

Alternatively, you may try out the GUI version of the program, found [here](https://github.com/luckytyphlosion/auto-tt-recorder-gui), which is more user friendly than the non-GUI program.

# Credits
* luckytyphlosion, the main writer of this program
* stebler, for making some gecko codes specifically for this project.
* WhatisLoaf, for his TT-Rec Tools and PyRKG
* Tockdom wiki, for MKW documentation
* SwareJonge, dragonbane0 and Dolphin devs, for Dolphin-Lua-Core
* Wiimm, for his ISO and SZS tools.
* The creators of all the codes used, credited in the gecko code template files in data/

If you contributed to this project in some way and I didn't list you, contact me and I'll add you here.

# Installation (for developers, i.e. people wanting to add new features)
Currently, these instructions only work for Windows. The two issues are that I do not have a Mac or Linux computer to thoroughly test the program, and this also means I cannot build the custom Dolphin-Lua-Core used for the program.

## Installation prerequisites
Install 7-Zip [here](https://www.7-zip.org/download.html). This is required to setup the repository and to create releases.

Firstly, download the latest release of the modified Dolphin-Lua-Core [here](https://github.com/luckytyphlosion/Dolphin-Lua-Core/releases/latest). Extract the contents such that it extracts to the folder `Dolphin-Lua-Core` containing the folders `Binary/x64`.

Alternatively, you may try building the modified Dolphin-Lua-Core yourself. There is no current comprehensive guide, but the installation notes on the Dolphin-Lua-Core repository state to "`use Microsoft Visual Studio 2015 Update 2 and Windows 10 SDK 10.0.10586.0`" (I have tried using "`Microsoft Visual Studio 2017 without any upgrades`" but it did not work for me).

Download the latest version of Python [here](https://www.python.org/downloads/). Just click the "Install Now" option. **You must check "Add python.exe to PATH"**.

Download this set of HQ Textures [here](https://drive.google.com/drive/folders/1j5zqfHjxFsemcD93iarzCFuBnMEa4jnT), and extract it. You will need to remember the path of the extracted folder for later.

## Cloning the repository
Optionally, make a fork of the repository, if you want to submit pull requests.

Clone the GitHub repository (either the main repo or the fork). You can either use GitHub Desktop to clone or use the command line. To clone with GitHub Desktop, firstly download the program [here](https://desktop.github.com/). Then, once the program is installed, open it, go to File (top left), click "Clone repository", go to the URL option, and paste in the URL of the GitHub repository you want to clone (either the main repo or the fork).

## Repository build options
In the location of the repository, create the following YAML file `build_options.yml`. Below is a description of how you should fill it in:

```yaml
# The path to the Dolphin-Lua-Core folder that you just downloaded.
# Below is an example, you need to fill it in with your own path
dolphin-lua-core-dirname: "C:/Users/User/Documents/GitHub/Dolphin-Lua-Core"

# The release version number. Must be of format "vN.N.N", where N is a number.
# Below is an example, you should fill it in with your own version number
release-name: v1.3.9

# Whether to build auto-tt-recorder specifically for Auto-TT-Recorder GUI.
# Keep this as is for now.
for-gui: false

# The path to the 7-Zip command line executable. Below is probably the correct path.
sevenz-filename: "C:/Program Files/7-Zip/7z.exe"
```

The following options are only relevant when running the test script, but they need to be specified or else the initialization script will throw an error.
```yaml
# The ids of which tests to run in test_ymls/, indicated by the start of each config's filename in test_ymls/.
# If this is empty (i.e. []), then run all tests.
# For now, just keep this as is.
include-tests: []

# Alternatively, if you want to run all tests except specific tests, then insert the ids of which tests you don't want to run here.
This only works if include-tests is empty.
# For now, just keep this as is.
exclude-tests: []

# Whether to test using the built release (with record_ghost.bat and all that). You must build the release first.
# For now, just keep this as is.
test-release: false

# The directory containing ISOs/WBFSs for all regions.
iso-directory: "C:/Users/User/Documents/RMCE 01"

# The filename of each ISO or WBFS in the above directory.
# Fill these with your own ISO filenames
# All ISOs are required to run the test script.
rmce01-iso: RMCE01.iso
rmcp01-iso: RMCP01.wbfs
rmcj01-iso: RMCJ01.wbfs
rmck01-iso: RMCK01.wbfs

# When testing for the release, determines whether to extract the 7z file for each test, or to use the previously extracted file.
# yes/true will always re-extract, random will do a coin flip whether to extract or not, and no/false will never re-extract.
release-clean-install: random

# The seed to use for randomizing the order of tests. Use 0 if you don't want to randomize the order.
randomize-tests-seed: 0

# Assume that the directories listed below have already been generated.
# After running the test script once, they stay generated, but keeping this as false helps to simulate a clean install.
assume-cmd-folders-exist: false

# Whether to delete the directories listed below even if they are not detected to be of the correct type.
# **This is a dangerous option as it can potentially delete most of your hard drive if you specify a wrong path.**
force-delete-invalid-directories: false

# Custom directories for the storage-folder, dolphin-folder, temp-folder,
# wiimm-folder, extra-hq-textures-folder, and chadsoft-cache-folder options.

# For each test, these directories are randomly assigned (with the posssibility of not being assigned at all)
# to test the robustness of each folder option.

# All of these directories, with the exception of extra-hq-textures-folder, will be
# created if they do not exist. If they do exist, the test script will attempt
# to delete them (except extra-hq-textures-folder), but only if it determines that
# they are of the folder type specified (so that you don't accidentally delete an important folder by mistake).

# Below are a description of what each suffix means:
# -absolute: The given path should be an absolute path.
# -relative: The given path should be a relative path, with the special parent path marker `..`.
#   The path is relative to the root of the repository, assuming that you are executing the test script within the root.
# -relative-no-parent: 

# The paths you can choose can be effectively anything as long as they abide by the above rules
# and they DO NOT overlap with the default paths for each option
# (so "storage" for storage-folder, "dolphin" for dolphin-folder, "temp" for temp-folder,
# and "bin/wiimm" for wiimm-folder), and they don't overlap with any other folder specified.

# Below are examples which you could theoretically use
# but there might be issues trying to create paths due to permissions.
# For relative paths without parent indicators, the initial directory
# should be "test_scratch", as it is defined within the .gitignore.

storage-folder-absolute: "C:/Users/User/auto-tt-recorder-gui-v0.2.1-win32-x64/resources/app/auto-tt-recorder_v1.3.2_for_gui/storage"
storage-folder-relative: "../../auto-t2t-rec-test_storage"
storage-folder-relative-no-parent: "sto2ring/a big store"

dolphin-folder-absolute: "c:/users/user/documents/auto_t2t_recorder/test_dolphin"
dolphin-folder-relative: "../../auto-tt-recorder2_v1.3.6/dolphin"
dolphin-folder-relative-no-parent: "test_scratch/test_dol2phin"

temp-folder-relative: "../../auto-tt-recorder_v1.3.2/t2emp"
temp-folder-absolute: "C:/users/user/pictures/aut2oTTtemp"
temp-folder-relative-no-parent: "test_scratch/te2mp2"

wiimm-folder-absolute: "C:/users/user/documents/RMCE 01/b2in ary"
wiimm-folder-relative: "../../auto_tt_recorder/w2iimm"
wiimm-folder-relative-no-parent: "test_scratch/bin2/wi2imm2"

# Fill this option with the HQ Textures folder you extracted earlier
extra-hq-textures-folder-absolute: "C:/users/user/documents/GitHub/auto-tt-recorder/hq_textures"

chadsoft-cache-folder-relative: "../not a git repo/chadsof"
chadsoft-cache-folder-relative-no-parent: test_scratch/one_folder/cache_dir_c2hadsoft
```

## Repository setup
Once you have finished setting up `build_options.yml`, open Powershell. Change directory to the location of the repository. By default, Powershell opens in `C:/Users/<user>`, where `<user>` is your Windows username, and GitHub Desktop will clone the repository to `C:/Users/<user>/Documents/GitHub/auto-tt-recorder`. So if both the above conditions are true, you can just do:
```bash
cd Documents/GitHub/auto-tt-recorder
```

If you have not installed `virtualenv`, run the following command:
```bash
pip install virtualenv
```

Create a virtual environment by running the following command:
```bash
virtualenv virt 
```

To enter the virtual environment, run the following commands. You will need to do this everytime you want to run the program if you have not entered the above created virtual environment (indicated in Powershell by a `(virt)` at the start of the command line prompt):
```ps1
Set-ExecutionPolicy RemoteSigned -Scope Process
.\virt\scripts\activate.ps1
```

Install the required python dependencies with the following command:
```bash
pip install -r requirements_win_record_ghost.txt
```

Run the following command to initialize the repository with certain executables (the modified Dolphin-Lua-Core, ffmpeg, ffprobe, wit, wszst, and wkmpt).

```bash
python setup_workspace.py
```

# Running the program

To run the program, run the following command:
```bash
python record_ghost.py -cfg <yourconfigfile.yml>
```

where `<yourconfigfile.yml>` is a config file as specified in [the documentation](https://github.com/luckytyphlosion/auto-tt-recorder/blob/master/docs/DOCS.md).

(You can also specify each option on the command line manually, but I have never used that feature ever since I created the program).

# Running tests

To run all the tests, run the following command:
```bash
python test_auto_tt_recorder.py
```

This will run tests based on the options in `build_options.yml`. All of the test configs are defined in `test_ymls/`. The test filename must start with an integer followed by an underscore to indicate the test id. Tests which are meant to fail have `test_fail` in the filename.

Note that currently, the test script does not report whether a test succeeded or not (only reporting whether an exception was thrown or not). You will need to check the output manually to see if the test was successful.

For tests that succeed, this means checking if the output video file was created and that the commands specified actually work. All of the commands that the config file is meant to test are described within the filename.

For tests that fail, this means checking the exception raised, and whether it corresponds to the expected exception. The filename indicates what is meant to fail, but the exact exception that the config expects to be thrown is not indicated anywhere.

# Building the release

To build the release, run the following command:
```bash
python package_release.py
```

This will create the files `release_working/auto-tt-recorder_{release-name}.7z` and `release_working/auto-tt-recorder_{release-name}.zip` containing the releases that are hosted on GitHub, where `release-name` is defined in `build_options.yml`

Please note that any releases are subject to the license (GPLv2+), which informally speaking states that any binary releases must be released with the source code as well. This is simple as pushing the source code to GitHub which corresponds to the release you create.

If `for-gui` in `build_options.yml` is `true`, then it will build a modified version of auto-tt-recorder designed for Auto-TT-Recorder GUI. Using this modified version may be covered later.

