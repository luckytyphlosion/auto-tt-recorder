# Dolphin.ini, GFX.ini

These files are base ini files which will be copied over to Dolphin's config folder if they do not already exist there. The options and headers which are set in each config file are fixed throughout the entire use of the program, i.e. the values in the config file will never be changed by the program. Below is a description of each option and its purpose for auto-tt-recorder.

## Dolphin.ini
### Analytics: Enabled = False

This controls whether analytics are sent to the Dolphin developers (via Internet). This is disabled since this is an outdated Dolphin build so there is no point in sending any statistics.

### Analytics: PermissionAsked = True

This controls whether Dolphin should display a message prompting the user to give permission to send analytics to Dolphin developers. It is disabled because the dialog box cannot be cleared programatically otherwise.

### Display: RenderToMain = True

This controls whether Dolphin renders the game in the main window, as opposed to a separate pop-out window. This is set to true as an option to hide the Dolphin window while auto-tt-recorder was recording was desired, and it would have been more work to add the ability to hide the game window to Dolphin, as opposed to just the main window.

### DSP, Movie

Ini headers related to sound and recording. This is needed as we set the DumpAudio and DumpFrames options to False every time the program is run, and the headers are there to make assigning the options easier.

### Interface: ConfirmStop = False

This controls whether Dolphin should display a dialog message when the user requests to stop the current game. It might be needed as exiting Dolphin via Lua might bring up this dialog message which would be impossible to clear programatically with Lua.

### Core: EnableCheats = True

This enables the use of Gecko cheat codes. This needs to be enabled as recording a time trial requires the use of multiple cheat codes.

## GFX.ini
### Hacks: EFBEmulateFormatChanges = True

While the exact nature of this option isn't fully understood (it's a toggle for whether to enable an emulation hack to speedup Dolphin), enabling this will force Dolphin to properly emulate some behaviour of the Wii, which prevents a blue box appearing on the top left of the screen.

### Settings: InternalResolutionFrameDumps = True

This option causes Dolphin to dump frames at the internal rendering resolution of the game, before it is downscaled to the Dolphin window. It is enabled so that dumps get the full resolution of the requested screen size without using an external program such as Infinite Screen.

# rksys.dat
A "blank" save file with the top left license registered. This is It is created by running Mario Kart Wii with no save file, creating a license using the top left slot, choosing the first Mii from the Guest list, completing the registration, and exiting Dolphin on the Mario Kart Wii main menu (where one can pick Single Player, Multiplayer etc. to play).

# RMCE01\_gecko\_codes_template.ini
Todo.
