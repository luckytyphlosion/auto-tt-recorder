Commands
===========
To add a command to the config.yml file, on an empty line (anywhere in the file), put the command name, followed by a colon and a space, followed by the command value. For example, `track-name: Desert Fort` would change the track name.

List of types and what they mean:
| Type | Description
|------|------------
|string| General text, e.g. `time_trial.mp4`, `"Desert Fort"`
|int|Number without a decimal part, e.g. `18`, `52428800`
|float|Number which can have a decimal part, e.g. `15.5`, `100`
|boolean|`true` or `false`

# Ghost related commands
## Main ghost commands
- **Only one** of `chadsoft-ghost-page`, `main-ghost-filename`, and `main-ghost-auto` can be specified.
- When `timeline` is `top10`, the following restrictions are placed (`main-ghost-auto` will follow the logic of the below options depending on whether it is a link or filename):
  - `chadsoft-ghost-page` can only be specified if either:
    - `top-10-gecko-code-filename` is specified
    - `top-10-highlight` is `-1` if `top-10-chadsoft` is specified
  - `main-ghost-filename` takes precedence over the ghost retreived by `top-10-chadsoft`
 
| Command | Type   | Description
|-----------------------------|--------|-----------------------------------------------------------------------------------------------------
| `chadsoft-ghost-page` | string | Link to the Chadsoft ghost page of the ghost to record. Specifying this will download the ghost file. In addition, if the track is a custom track, the program will automatically download the szs file from [Wiimm's Custom Track Archive](https://ct.wiimm.de/). See above for when this option is not valid.
| `main-ghost-filename` | string   | Filename of the main ghost to record. Takes precedence over the ghost retrieved by `top-10-chadsoft` if it is specified. See above for when this option is not valid.
| `main-ghost-auto` | string | Smart option which is just `main-ghost-filename` and `chadsoft-ghost-page` combined. Will automatically detect which option to use, based on the option input (i.e. chadsoft link will use `chadsoft-ghost-page`, otherwise assumes `main-ghost-filename`). See above for when this option is not valid.
|<img width=250/>| |

## Comparison ghost commands
- **Only one** of `chadsoft-comparison-ghost-page`, `comparison-ghost-filename`, and `comparison-ghost-auto` can be specified.

| Command | Type   | Description
|-----------------------------|--------|-----------------------------------------------------------------------------------------------------
| `chadsoft-comparison-ghost-page` | string | Link to the Chadsoft ghost page of the ghost to compare against. This cannot be specified with the other options in this table.
| `comparison-ghost-filename` | string | Filename of the comparison ghost. This cannot be specified with the other options in this table.
| `comparison-ghost-auto` | string | Smart option which is just `comparison-ghost-filename` and `chadsoft-comparison-ghost-page` combined. Will automatically detect which option to use, based on the option input (i.e. chadsoft link will use `chadsoft-comparison-ghost-page`, otherwise assumes `comparison-ghost-filename`). This cannot be specified with the other options in this table.
|<img width=250/>| |

# Input/output filenames and 200cc
| Command | Type   | Description
|-----------------------------|--------|-----------------------------------------------------------------------------------------------------
| `iso-filename` | string | Filename of the Mario Kart Wii ISO or WBFS. Note that NKIT is not supported.
| `szs-filename` | string | Filename of the szs file corresponding to the ghost file, if recording for a custom track. **You do not need to specify this if you specify `chadsoft-ghost-page` or `top-10-chadsoft` (with exceptions).** Exception: tracks are automatically downloaded from [Wiimm's Custom Track Archive](https://ct.wiimm.de/), but some tracks are not available. In that case, specifying the szs filename is required.
| `output-video-filename` | string   | Filename of the output recorded ghost. All possible allowed formats are `mkv`, `webm`, and `mp4`. See [Encoding related commands](#encoding-related-commands) for details on restrictions.
| `on-200cc` | boolean | Forces the use of 200cc, regardless if the ghost was set on 200cc or not. If neither `on-200cc` nor `no-200cc` is set, auto-tt-recorder will automatically detect 150cc or 200cc if `chadsoft-ghost-page` or `top-10-chadsoft` is specified, otherwise it will assume 150cc.
| `no-200cc` | boolean | Forces the use of 150cc, regardless if the ghost was set on 150cc or not. If neither `on-200cc` nor `no-200cc` is set, auto-tt-recorder will automatically detect 150cc or 200cc if `chadsoft-ghost-page` or `top-10-chadsoft` is specified, otherwise it will assume 150cc.
|<img width=250/>| |

# Timeline related commands
| Command | Type   | Description                                                                                         |
|-----------------------------|--------|-----------------------------------------------------------------------------------------------------|
| `timeline` | string | Choice of recording timeline to use. Possible options are below. Default is `noencode`.
|            | noencode | Race footage only, fastest to dump, just packages the raw frame and audio dump into an mkv file, no support for editing
|            | ghostonly | Race footage only, but supports all the editing options available for the race, e.g. fade in/out, input display
|            | ghostselect | Records starting from the Time Trial Ghost Select Screen
|            | mkchannel | Records from the Mario Kart Channel Race Ghost Screen
|            | top10 | Records a Custom Top 10 into the Mario Kart Channel Race Ghost Screen


## Non-top10 related timeline commands
| Command | Type   | Description                                                                                         |
|-----------------------------|--------|-----------------------------------------------------------------------------------------------------|
| `mk-channel-ghost-description` | string | The description of the ghost which appears on the top left of the Mario Kart Channel Race Ghost Screen. Applies for timelines `mkchannel` and `top10`. Default is `Ghost Data`.
| `track-name` | string | The name of the track. This will affect the track name shown on the ghost description page, seen in all timelines except `noencode` and `ghostonly`. If `auto` is specified, the program will try to automatically get the track name from any chadsoft link if provided (either `chadsoft-ghost-page`, `chadsoft-comparison-ghost-page`, or `top-10-chadsoft`). If no chadsoft link is provided and `szs-filename` is not specified, then assumes a vanilla track and uses the vanilla name. If omitted or null, uses the track name of the rkg track slot.
|<img width=250/>| |

## Top10 related timeline commands
| Command | Type   | Description                                                                                         |
|-----------------------------|--------|-----------------------------------------------------------------------------------------------------|
| `top-10-chadsoft` | string | Chadsoft link for the custom top 10 leaderboard. Current supported filters are the filters that Chadsoft supports, i.e. Region, Vehicles, and Times. Specifying this will download the ghost file based on the ghost highlighted by `top-10-highlight`. In addition, if the track is a custom track, the program will automatically download the szs file from [Wiimm's Custom Track Archive](https://ct.wiimm.de/). This cannot be specified with `top-10-gecko-code-filename`, or `chadsoft-ghost-page` UNLESS `top-10-highlight` is `-1`.
| `top-10-location` | string | What portion of the globe will show on the top 10 screen. Possible options are `ww`/`worldwide` for the 3d globe, or a location option from the allowed options at https://www.tt-rec.com/customtop10/. If `top-10-gecko-code-filename` is specified instead, then the possible options are `ww`/`worldwide` for the 3d globe, and anything else to show the regional globe. Default is `ww`.
| `top-10-title` | string | The title that shows at the top of the Top 10 Leaderboard. Default is `Worldwide Top 10` for worldwide, and `<Location> Top 10` for the specified location. Ignored if `top-10-gecko-code-filename` is specified.
| `top-10-highlight` | int | The entry to highlight on the Top 10 Leaderboard. Must be in range `1`-`10`, or `-1` for no highlight. Default is `1`. Ignored if `top-10-gecko-code-filename` is specified.
| `top-10-censors` | string | Chadsoft player IDs of the players to censor on the top 10 screen (replace with Player), separated by spaces. The player ID can be retrieved from the chadsoft player page. Ignored if `top-10-gecko-code-filename` is specified.
| `top-10-gecko-code-filename` | string | The filename of the file containing the gecko code used to make a Custom Top 10. This cannot be specified with `top-10-chadsoft`. If your Top 10 is anything more complicated than a chadsoft leaderboard, then you're better off using https://www.tt-rec.com/customtop10/ to make your Custom Top 10.
|<img width=250/>| |

# Presentation/Editing related commands
## Audio related
| Command | Type   | Description                                                                                         |
|-----------------------------|--------|-----------------------------------------------------------------------------------------------------|
| `no-music` | boolean | Disable BGM and don't replace it with music.
| `music-filename` | string | Filename of the music which will replace the regular BGM. Specifying `bgm` will keep the regular BGM. Specifying an empty string or `None`/`none` will disable music altogether. The default is `bgm`.
| `game-volume` | float | Multiplicative factor to control game volume in the output video (e.g. `0.5` to halve the game volume). Default is `0.6`. Ignored if no music is specified.
| `music-volume` | float | Multiplicative factor to control music volume in the output video (e.g. `0.5` to halve the music volume). Default is `1.0`. Ignored if no music is specified.
|<img width=250/>| |

## "Overlay" related
| Command | Type   | Description                                                                                         |
|-----------------------------|--------|-----------------------------------------------------------------------------------------------------|
| `input-display` | string | Whether to include the input display in the output video. Currently supported options are `auto`, `classic`, `gcn`, `nunchuck`, and `none` (for no input display). `auto` will automatically try to detect the controller type to use for the input display, but this only works if a chadsoft ghost link or chadsoft leaderboard is provided. Additionally, the controller detected must not be the Wii Wheel as it is not implemented. Otherwise, `auto` will default to `gcn`. The rest of the controllers may be supported in the future. Default is `none`.
| `speedometer` | string | Enables speedometer and takes in an argument for the SOM display type. Possible values are below. Default is `none`.
|               | fancy | Left aligned, special km/h symbol using a custom Race.szs, looks bad at 480p, 0-1 decimal places allowed
|               | regular | Left aligned, "plain-looking" km/h symbol, usable at 480p, 0-2 decimal places allowed
|               | standard | The original pretty speedometer, right aligned. 
|               | none | Do not include a speedometer.
| `speedometer-metric` | string | What metric of speed the speedometer reports. Possible options are below. Default is `engine`.
|                      | engine | The speed which the vehicle engine is producing (ignoring external factors like Toad's Factory conveyers)
|                      | xyz | The norm of the current position minus the previous position
|                      | xz | Like xyz except the vehicle's y position is not taken into account (speed won't increase when falling). Default is engine.
| `speedometer-decimal-places` | int | The number of decimal places in the speedometer. Default depends on the speedometer used. Below specifies information on the valid values for this option.
|                              | fancy | Valid values: 0-1. Default is 1
|                              | regular | Valid values: 0-2. Default is 2
|                              | standard | Ignored (always forced to 2)
| `ending-message` | string | The ending message that shows on the bottom left after completing a time trial. Default is `Video recorded by Auto TT Recorder`.
|<img width=250/>| |

## "High quality" related
| Command | Type   | Description                                                                                         |
|-----------------------------|--------|-----------------------------------------------------------------------------------------------------|
| `dolphin-resolution` | string | Internal resolution for Dolphin to render at. Possible options are `480p`, `720p`, `1080p`, `1440p`, and `2160p`. Default is `480p` (966x528)
| `no-background-blur` | boolean | If enabled, on most tracks, the blurry/fuzzy background images are now sharp and clear. **Warning:** On certain tracks, enabling this will cause the track to look blurry. Known tracks: Underground Sky, Big Express City.
| `no-bloom` | boolean | If enabled, disables the "bloom" effect ([Wikipedia](https://en.wikipedia.org/wiki/Bloom_(shader_effect))). The effect is notable for not rendering properly on resolutions higher than 480p. Disabling bloom will cause graphics to look sharper however textures will have increased contrast which may be a negative depending on the viewer.
| `hq-textures` | boolean | Whether to enable HQ textures. Current built-in HQ textures supported are the Item Slot Mushrooms. Looks bad at 480p.
| `extra-hq-textures-folder` | string | The folder containing any extra HQ textures you want. If omitted or `null`, don't load any extra textures. Note that `hq-textures` needs to be enabled for the textures to be loaded. Technical Note: The program loads the texture files by copying them over to the dolphin textures folder located at `User/Load/Textures`. To avoid unnecessary copies every time the program is run, the program checks if the texture file has already been copied by comparing when each file was last modified. If the source and dest file have different timestamps, then it is copied over.
| `use-ffv1` | boolean | Whether to use the lossless ffv1 codec. Note that an ffv1 dump has the exact same quality as an uncompressed dump, i.e. they are exactly the same pixel-by-pixel. This probably doesn't matter as YouTube will heavily compress uploaded videos anyway, but scientific tests haven't been done yet.
|<img width=250/>| |

# Encoding related commands
| Command | Type   | Description                                                                                         |
|-----------------------------|--------|-----------------------------------------------------------------------------------------------------|
| `encode-type` | string | Type of encoding to perform. Valid options are `crf` for a constant quality encode, and `size` for a constrained size based output. Pick `crf` if you're uploading to YouTube or if you're viewing the recording offline, and pick `size` if you plan to upload to a place with size limits like Discord.
| `crf-value` | float | Crf value to pass to ffmpeg. Valid range is 0-51. Default is 18. Lower values provide higher quality at the cost of file size.
| `h26x-preset` | string | H.26x preset option which will be passed to ffmpeg. Ignored for non-crf based encodes. This option basically controls how fast encoding is, at the cost of filesize. Faster options might also lower the quality. Valid options are `ultrafast`, `superfast`, `veryfast`, `faster`, `fast`, `medium`, `slow`, `slower`, `veryslow`, and `placebo`. Default is `medium`. Recommended option is `slow`.
| `video-codec` | string | Video codec to encode the output video. For crf-based encodes, valid options are `libx264` and `libx265`, and the default is `libx264`. For constrained size-based encodes, valid options are `libx264` and `libvpx-vp9`, and the default is `libvpx-vp9`. The difference between `libx264` and `libx265` results in a smaller file size at the same quality at the cost of encoding time (unscientific tests suggest a speed decrease of 10x). `libx265` will also not play in browsers or Discord. Other codecs may be supported in the future.
| `audio-codec` | string | Audio codec to encode the audio of the output video. Valid options are `aac` and `libopus`. `libopus` results in higher quality and a lower file size than `aac` so it should be chosen for almost all use cases, the only reason that `aac` should be selected is if the desired output file is mp4 and maximizing compatibility across devices is desired. That being said, `libopus` in mp4 has been tested to work in VLC, PotPlayer, Discord client, Chrome, Firefox, and Discord on Android, and does not work with Windows Media Player or Discord on iOS. The default is `aac` for crf encoded mp4 files, `libopus` for size-based encoded mp4 files, and `libopus` for mkv and webm files.
| `encode-size` | int | Max video size allowed, in bytes. Currently only used for constrained size-based encodes (2-pass VBR) encoding (`encode-type` of `size`). Default is `52428800` (50MiB, max size that Discord will embed videos passed as a link)
| `audio-bitrate` | string | Audio bitrate for encodes. Higher bitrate means better audio quality. Specified value can be an integer or an integer followed by k (multiplies by 1000). For crf-based encodes, the default is `128k` for libopus, and `384k` for aac. For constrained size-based encodes, the default is `64k` for libopus, and `128k` for aac.
| `pixel-format` | string | Pixel format of the output video. Default is `yuv420p`. This input is not validated against! If unsure, don't specify this option.
| `output-width` | int | Width of the output video. If omitted, don't rescale the video at all.
| `aspect-ratio-16-by-9` | boolean | Whether to make the output video aspect ratio 16:9. Dolphin dumps at slightly less than 16:9, which causes black bars to appear in YouTube thumbnails and in full screen. Not recommended if uploading to Discord or recording for offline purposes. Default is `true` for crf-based encodes and `false` for size-based encodes. Specifying `null` also enables this behaviour.
| `youtube-settings` | boolean | Add some encoding settings recommended by YouTube. This might increase quality on YouTube's end. Ignored for size based encodes.
|<img width=250/>| |

# Enhancement related commands
| Command | Type   | Description                                                                                         |
|-----------------------------|--------|-----------------------------------------------------------------------------------------------------|
| `extra-gecko-codes-filename` | string | The filename of the file containing any extra gecko codes you want when recording. Not enabled during the `top 10`/`mkchannel` screen. It is your responsibility to make sure the gecko codes file is formatted correctly (this might change in the future) as well as to not specify any conflicting codes. Specifying the MSG Editor gecko code will probably cause issues as only one code can be used at a time. Omit this if you don't want any extra gecko codes.

# Misc/debug commands
| Command | Type   | Description                                                                                         |
|-----------------------------|--------|-----------------------------------------------------------------------------------------------------|
| `ffmpeg-filename` | string | Path to the ffmpeg executable to use. Default is `ffmpeg` (use system ffmpeg).
| `ffprobe-filename` | string | Path to the ffprobe executable to use. Default is `ffprobe` (use system ffprobe).
| `keep-window` | boolean | By default, the Dolphin executable used to record the ghost is hidden to prevent accidental interaction with the window. Enabling this option will keep the window open, e.g. for debugging.
| `encode-only` | boolean | Assume that all necessary frame dumps already exist, instead of running Dolphin to dump out frames. Useful for testing in case an error occurs through the encoding stage.
| `dolphin-volume` | int | Volume of the Dolphin executable. Only relevant for debugging, has no impact on audiodump volume.
| `chadsoft-read-cache` | string | Whether to read any data downloaded from Chadsoft and saved to a local cache folder. Cache purging is disabled if this option is false.
| `chadsoft-write-cache` | string | Whether to save any data downloaded from Chadsoft to a local cache folder to avoid needing to redownload the same files.
| `chadsoft-cache-expiry` | string | Duration until data downloaded from Chadsoft expires and is purged. Example formats: 1h23m46s, 24h, 3h30m, 1000 (seconds implied), 90m100s. The duration is applied on a per-file basis, so if the expiry time is 24h, each file will be deleted 24h after the specific file was downloaded. Note that the cache is purged when the program is run regardless of whether the purged files would have been requested or not. Default is 24h. Cache purging can be disabled if this option evaluates to 0 or if `chadsoft-read-cache` is unspecified or false.
| `input-display-dont-create` | boolean | If enabled, assumes that the video file for the input display has already been created. Only relevant for debugging.
|<img width=250/>| |






