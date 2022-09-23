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

import subprocess
import ffmpeg
import os
import re
import pathlib
import platform

import job_process
import PyRKG.VideoGenerator

from stateclasses.timeline_classes import *
from stateclasses.encode_classes import *
from stateclasses.music_option_classes import *
from stateclasses.input_display import *

nb_frames_regex = re.compile(r"^nb_frames=([0-9]+)", flags=re.MULTILINE)

dev_null = "/dev/null" if os.name == "posix" else "NUL"

platform_system = platform.system()

FPS = 59.94005994006

class DynamicFilterArgs:
    __slots__ = ("adelay_frame_value", "fade_start_frame", "trim_start_frame", "input_display_start_frame")

    def __init__(self, adelay_frame_value, fade_start_frame, trim_start_frame, input_display_start_frame):
        self.adelay_frame_value = adelay_frame_value
        self.fade_start_frame = fade_start_frame
        self.trim_start_frame = trim_start_frame
        self.input_display_start_frame = input_display_start_frame

FROM_TT_GHOST_SELECT_TRACK_LOADING_BLACK_SCREEN_FRAME_TIMESTAMP = 186
FROM_TT_GHOST_SELECT_TRACK_LOADING_BLACK_SCREEN_TIMESTAMP = FROM_TT_GHOST_SELECT_TRACK_LOADING_BLACK_SCREEN_FRAME_TIMESTAMP/59.94005994006

class InputDisplayGfxInfo:
    __slots__ = ("input_box_filename", "box_x", "box_y", "inputs_x", "inputs_y", "inputs_width", "inputs_height")

    def __init__(self, input_box_filename, inputs_width, inputs_height, inputs_x, inputs_y, box_x, box_y):
        self.input_box_filename = input_box_filename
        self.inputs_width = inputs_width
        self.inputs_height = inputs_height
        self.inputs_x = inputs_x
        self.inputs_y = inputs_y
        self.box_x = box_x
        self.box_y = box_y

# positions and scaling were manually calculated
# these are not centered by any means, and are some pixels off for each resolution
dolphin_resolution_to_input_display_gfx_info = {
    "480p": InputDisplayGfxInfo("data/input_box_480p.png", 203, 127, 22, 361, 32, 366),
    "720p": InputDisplayGfxInfo("data/input_box_720p.png", None, None, 56, 724, 75, 734),
    "1080p": InputDisplayGfxInfo("data/input_box_1080p.png", 608, 380, 76, 1082, 106, 1102),
    "1440p": InputDisplayGfxInfo("data/input_box_2k.png", 810, 516, 88, 1447, 129, 1471),
    "2160p": InputDisplayGfxInfo("data/input_box.png", 1216, 769, 148, 2161, 209, 2195),
}

#ENABLE_EQUALS = 
class Encoder:
    __slots__ = ("ffmpeg_filename", "ffprobe_filename", "dolphin_resolution", "music_option", "timeline_settings", "video_frame_durations", "print_cmd")

    def __init__(self, ffmpeg_filename, ffprobe_filename, dolphin_resolution, music_option, timeline_settings, print_cmd=False):
        self.ffmpeg_filename = ffmpeg_filename
        self.ffprobe_filename = ffprobe_filename
        self.dolphin_resolution = dolphin_resolution
        self.music_option = music_option
        self.timeline_settings = timeline_settings
        self.video_frame_durations = {}
        self.print_cmd = print_cmd

    def get_video_frame_duration(self, video_file="dolphin/User/Dump/Frames/framedump0.avi"):
        video_frame_duration = self.video_frame_durations.get(video_file)
        if video_frame_duration is not None:
            return video_frame_duration

        framedump_ffprobe_output = subprocess.check_output((self.ffprobe_filename, "-v", "0", "-select_streams", "v", "-show_entries", "stream=nb_frames", video_file), stderr=subprocess.STDOUT).decode(encoding="ascii")

        nb_frames_match_obj = nb_frames_regex.search(framedump_ffprobe_output)
        if not nb_frames_match_obj:
            raise RuntimeError("FFmpeg command did not return dspdump.wav audio duration!")

        video_frame_duration = int(nb_frames_match_obj.group(1))

        self.video_frame_durations[video_file] = video_frame_duration
        return video_frame_duration

    def encode_stream_copy(self, output_video_filename):
        ffmpeg_stream_copy_cmd = (self.ffmpeg_filename, "-y", "-i", "dolphin/User/Dump/Frames/framedump0.avi", "-i", "dolphin/User/Dump/Audio/dspdump.wav", "-c", "copy", output_video_filename)

        if platform_system == "Windows":
            job_process.run_subprocess_as_job(ffmpeg_stream_copy_cmd)
        else:
            subprocess.run(
                ffmpeg_stream_copy_cmd, check=True
            )

    def gen_dynamic_filter_args(self, fade_frame_duration):
        output_params = {}
    
        with open("dolphin/output_params.txt", "r") as f:
            for line in f:
                if line.strip() == "":
                    continue
    
                param_name, param_value = line.split(": ", maxsplit=1)
                output_params[param_name] = param_value.strip()
    
        frame_replay_starts = int(output_params["frameReplayStarts"])
        frame_recording_starts = int(output_params["frameRecordingStarts"])
    
        adelay_frame_value = frame_replay_starts - frame_recording_starts
        video_frame_len = self.get_video_frame_duration()
        fade_start_frame = video_frame_len - fade_frame_duration
        trim_start_frame = frame_replay_starts - frame_recording_starts

        frame_input_starts = int(output_params["frameInputStarts"])

        input_display_start_frame = frame_input_starts - frame_recording_starts

        return DynamicFilterArgs(adelay_frame_value, fade_start_frame, trim_start_frame, input_display_start_frame)


    def add_input_display_to_video(self, video_in_file, dynamic_filter_args):
        video_generator = PyRKG.VideoGenerator.VideoGenerator("classic", self.timeline_settings.input_display.rkg_file_or_data)
        print("Generating input display!")
        if not self.timeline_settings.input_display.dont_create:
            video_generator.run("temp/input_display.mov", self.ffmpeg_filename)
        input_display_frame_duration = video_generator.inputs.get_total_frame_nr()

        input_display_gfx_info = dolphin_resolution_to_input_display_gfx_info[self.dolphin_resolution]
        input_box_in_file = ffmpeg.input(input_display_gfx_info.input_box_filename)

        input_display_start_frame = dynamic_filter_args.input_display_start_frame
        input_display_end_frame = input_display_start_frame + input_display_frame_duration - 1

        #input_box_shifted = input_box_in_file#.setpts(f"PTS-STARTPTS+{input_display_start_frame}")

        box_on_video = ffmpeg.filter(
            (video_in_file, input_box_in_file),
            "overlay",
            enable=f"between(t,{input_display_start_frame/FPS},{input_display_end_frame/FPS})",
            x=input_display_gfx_info.box_x, y=input_display_gfx_info.box_y,
            eval="init"
        ).setpts(f"PTS-STARTPTS")

        input_display_in_file = ffmpeg.input("temp/input_display.mov")

        if input_display_gfx_info.inputs_width is not None:
            scaled_input_display = ffmpeg.filter(input_display_in_file, "scale",
                input_display_gfx_info.inputs_width, input_display_gfx_info.inputs_height, flags="bicubic"
            )
        else:
            scaled_input_display = input_display_in_file

        # +{input_display_start_frame/60}/TB
        # {input_display_start_frame}
        print(f"input_display_start_frame: {input_display_start_frame}")
        scaled_input_display_shifted = scaled_input_display.setpts(f"PTS-STARTPTS+{input_display_start_frame/FPS}/TB")
        video_with_input_display = ffmpeg.filter(
            (box_on_video, scaled_input_display_shifted),
            "overlay",
            enable=f"between(t,{input_display_start_frame/FPS},{input_display_end_frame/FPS})",
            x=input_display_gfx_info.inputs_x, y=input_display_gfx_info.inputs_y,
            eof_action="pass", eval="init"
        )

        return video_with_input_display

    def encode_complex_common(self, secondary_video_in_file, secondary_audio_in_file):
        dolphin_resolution = self.dolphin_resolution
        music_option = self.music_option
        timeline_settings = self.timeline_settings

        encode_settings = timeline_settings.encode_settings
        fade_frame_duration = encode_settings.fade_frame_duration

        dynamic_filter_args = self.gen_dynamic_filter_args(fade_frame_duration)

        video_in_file = ffmpeg.input("dolphin/User/Dump/Frames/framedump0.avi")
        audio_in_file = ffmpeg.input("dolphin/User/Dump/Audio/dspdump.wav")

        if music_option.option == MUSIC_CUSTOM_MUSIC:
            music_in_file = ffmpeg.input(music_option.music_filename).audio
            if encode_settings.music_volume == 1.0:
                music_volume_stream = music_in_file
            else:
                music_volume_stream = ffmpeg.filter(music_in_file, "volume", volume=encode_settings.music_volume)
            game_volume_stream = ffmpeg.filter(audio_in_file, "volume", volume=encode_settings.game_volume)
            audio_combined_stream = ffmpeg.filter([game_volume_stream, music_volume_stream], "amix", inputs=2, duration="first")            
        else:
            audio_combined_stream = audio_in_file

        if timeline_settings.input_display.type == INPUT_DISPLAY_CLASSIC:
            video_with_input_display = self.add_input_display_to_video(video_in_file, dynamic_filter_args)
        elif timeline_settings.input_display.type == INPUT_DISPLAY_NONE:
            video_with_input_display = video_in_file
        else:
            assert False

        video_faded_stream = ffmpeg.filter(video_with_input_display, "fade", type="out", duration=fade_frame_duration/FPS, start_time=dynamic_filter_args.fade_start_frame/FPS)
    
        audio_combined_faded_stream = ffmpeg.filter(audio_combined_stream, "afade", type="out", duration=fade_frame_duration/FPS, start_time=dynamic_filter_args.fade_start_frame/FPS)

        if secondary_video_in_file is not None and secondary_audio_in_file is not None:
            all_streams = [
                secondary_video_in_file,
                secondary_audio_in_file,
                video_faded_stream,
                audio_combined_faded_stream
            ]
    
            almost_final_streams = ffmpeg.filter_multi_output(all_streams, "concat", n=2, v=1, a=1)
            almost_final_video_stream = almost_final_streams[0]
            final_audio_stream = almost_final_streams[1]
        else:
            almost_final_video_stream = video_faded_stream
            final_audio_stream = audio_combined_faded_stream

        if encode_settings.output_width is not None:
            final_video_stream = ffmpeg.filter(almost_final_video_stream, "scale", encode_settings.output_width, "trunc(ow/a/2)*2", flags="bicubic")
        else:
            final_video_stream = ffmpeg.filter(almost_final_video_stream, "crop", "trunc(iw/2)*2", "trunc(ih/2)*2")

        return final_video_stream, final_audio_stream, dynamic_filter_args

    def encode_from_top_10_leaderboard(self):
        top_10_video_in_file = ffmpeg.input("dolphin/User/Dump/Frames/top10.avi")
        top_10_audio_in_file = ffmpeg.input("dolphin/User/Dump/Audio/top10.wav")

        return self.encode_complex_common(top_10_video_in_file, top_10_audio_in_file)

    def encode_from_tt_ghost_select(self):
        tt_ghost_select_video_in_file = ffmpeg.input("dolphin/User/Dump/Frames/tt_ghost_select.avi")
        tt_ghost_select_audio_in_file = ffmpeg.input("dolphin/User/Dump/Audio/tt_ghost_select.wav")

        return self.encode_complex_common(tt_ghost_select_video_in_file, tt_ghost_select_audio_in_file)

    def encode_complex(self, output_video_filename):
        dolphin_resolution = self.dolphin_resolution
        music_option = self.music_option
        timeline_settings = self.timeline_settings

        encode_settings = timeline_settings.encode_settings

        if timeline_settings.type == TIMELINE_GHOST_ONLY:
            final_video_stream, final_audio_stream, dynamic_filter_args = self.encode_complex_common(None, None)
        elif timeline_settings.type == TIMELINE_FROM_TT_GHOST_SELECTION:
            final_video_stream, final_audio_stream, dynamic_filter_args = self.encode_from_tt_ghost_select()
        elif timeline_settings.type in (TIMELINE_FROM_TOP_10_LEADERBOARD, TIMELINE_FROM_MK_CHANNEL_GHOST_SCREEN):
            final_video_stream, final_audio_stream, dynamic_filter_args = self.encode_from_top_10_leaderboard()
        else:
            raise RuntimeError(f"Unknown timeline type \"{timeline_settings.type}\"!")

        #final_video_stream = 
        if encode_settings.type == ENCODE_TYPE_CRF:
            ffmpeg_output_kwargs = {
                "vcodec": encode_settings.video_codec,
                "crf": encode_settings.crf,
                "acodec": encode_settings.audio_codec,
                "audio_bitrate": encode_settings.audio_bitrate,
                "pix_fmt": encode_settings.pix_fmt,
                "preset": encode_settings.h26x_preset
            }
            if encode_settings.output_format == "mp4":
                if encode_settings.audio_codec == "libopus":
                    ffmpeg_output_kwargs["strict"] = "-2"
                ffmpeg_output_kwargs["movflags"] = "+faststart"

            if encode_settings.youtube_settings:
                if encode_settings.video_codec == "libx264":
                    ffmpeg_output_kwargs.update({
                        "bf": 2,
                        "g": 30,
                        "profile:v": "high"
                    })
                elif encode_settings.video_codec == "libx265":
                    ffmpeg_output_kwargs["x265-params"] = "no-open-gop=1:keyint=30:bframes=2"
                else:
                    assert False

            output_stream = ffmpeg.output(final_video_stream, final_audio_stream, output_video_filename, **ffmpeg_output_kwargs)
            if platform_system == "Windows":
                ffmpeg_final_command = ffmpeg.compile(output_stream, cmd=self.ffmpeg_filename, overwrite_output=True)
                job_process.run_subprocess_as_job(ffmpeg_final_command)
            else:
                ffmpeg.run(output_stream, cmd=self.ffmpeg_filename, overwrite_output=True)
        elif encode_settings.type == ENCODE_TYPE_SIZE_BASED:
            encode_size_bits = encode_settings.encode_size * 8
            if timeline_settings.type == TIMELINE_FROM_TT_GHOST_SELECTION:
                run_frame_len = self.get_video_frame_duration() + self.get_video_frame_duration("dolphin/User/Dump/Frames/tt_ghost_select.avi")
            elif timeline_settings.type in (TIMELINE_FROM_TOP_10_LEADERBOARD, TIMELINE_FROM_MK_CHANNEL_GHOST_SCREEN):
                run_frame_len = self.get_video_frame_duration() + self.get_video_frame_duration("dolphin/User/Dump/Frames/top10.avi")
            else:
                assert False

            print(f"run_frame_len: {run_frame_len}, run_len: {run_frame_len/FPS}")
            if encode_settings.video_codec == "libx264":
                dampening_factor = 0.98
            else:
                dampening_factor = 0.99

            avg_video_bitrate = int(dampening_factor * (encode_size_bits*FPS/run_frame_len - encode_settings.audio_bitrate))

            ffmpeg_output_kwargs = {
                "vcodec": encode_settings.video_codec,
                "video_bitrate": avg_video_bitrate,
                "pix_fmt": encode_settings.pix_fmt
            }

            if encode_settings.video_codec == "libvpx-vp9":
                ffmpeg_output_kwargs.update({
                    "row-mt": 1,
                    "threads": 8
                })
            elif encode_settings.video_codec == "libx264":
                ffmpeg_output_kwargs["preset"] = "slow"
            else:
                assert False

            if encode_settings.output_format == "mp4":
                ffmpeg_output_kwargs["movflags"] = "+faststart"

            ffmpeg_output_kwargs_pass1 = ffmpeg_output_kwargs.copy()
            ffmpeg_output_kwargs_pass1.update({
                "pass": 1,
                "format": "null",
                "an": None
            })

            output_stream_pass1 = ffmpeg.output(final_video_stream, dev_null, **ffmpeg_output_kwargs_pass1)

            ffmpeg_output_kwargs_pass2 = ffmpeg_output_kwargs.copy()
            ffmpeg_output_kwargs_pass2.update({
                "acodec": encode_settings.audio_codec,
                "audio_bitrate": encode_settings.audio_bitrate,
                "pass": 2
            })

            # ffmpeg segfaults when doing a 2 pass encoding with mp4???
            # but it works fine with mkv
            # so do a 2 pass using libx264 in mkv, then stream copy to mp4
            if encode_settings.output_format == "mp4":
                output_video_filepath_as_mkv = pathlib.Path(output_video_filename).with_suffix(".mkv")
                tentative_output_video_filename = str(output_video_filepath_as_mkv)
            else:
                tentative_output_video_filename = output_video_filename

            output_stream_pass2 = ffmpeg.output(final_video_stream, final_audio_stream, tentative_output_video_filename, **ffmpeg_output_kwargs_pass2)
            
            if platform_system == "Windows":
                pass1_command = ffmpeg.compile(output_stream_pass1, cmd=self.ffmpeg_filename, overwrite_output=True)
                job_process.run_subprocess_as_job(pass1_command)
                pass2_command = ffmpeg.compile(output_stream_pass2, cmd=self.ffmpeg_filename, overwrite_output=True)
                job_process.run_subprocess_as_job(pass2_command)

            else:
                ffmpeg.run(output_stream_pass1, cmd=self.ffmpeg_filename, overwrite_output=True)
                ffmpeg.run(output_stream_pass2, cmd=self.ffmpeg_filename, overwrite_output=True)

            if encode_settings.output_format == "mp4":
                mkv_to_mp4_args = [self.ffmpeg_filename, "-y", "-i", tentative_output_video_filename, "-c", "copy"]
                if encode_settings.audio_codec == "libopus":
                    mkv_to_mp4_args.extend(("-strict", "-2"))

                # -strict -2 must be before output video
                mkv_to_mp4_args.append(output_video_filename)

                if platform_system == "Windows":
                    job_process.run_subprocess_as_job(mkv_to_mp4_args)
                else:
                    subprocess.run(mkv_to_mp4_args, check=True)
                output_video_filepath_as_mkv.unlink(missing_ok=True)
        else:
            assert False

    def encode(self, output_video_filename):
        output_video_path = pathlib.Path(output_video_filename)
        output_video_path.parent.mkdir(parents=True, exist_ok=True)

        if self.timeline_settings.type == TIMELINE_NO_ENCODE:
            self.encode_stream_copy(output_video_filename)
        elif self.timeline_settings.type in (TIMELINE_GHOST_ONLY, TIMELINE_FROM_TT_GHOST_SELECTION, TIMELINE_FROM_TOP_10_LEADERBOARD, TIMELINE_FROM_MK_CHANNEL_GHOST_SCREEN):
            self.encode_complex(output_video_filename)
        else:
            raise RuntimeError("Unimplemented timeline settings type!")

#     return f"[2:a]adelay={adelay_value}|{adelay_value}[music_delayed];\
# [1:a]volume=0.6[game_audio_voldown];\
# [game_audio_voldown][music_delayed]amix=inputs=2:duration=first[audio_combined];\
# [0:v]fade=type=out:duration={fade_duration}:start_time={fade_start_time},split[video_faded_out1][video_faded_out2];\
# [audio_combined]afade=type=out:duration={fade_duration}:start_time={fade_start_time},asplit[audio_combined_faded_out1][audio_combined_faded_out2];\
# [video_faded_out1]trim=end=3.1,setpts=PTS-STARTPTS[v0];\
# [audio_combined_faded_out1]atrim=end=3.1,asetpts=PTS-STARTPTS[a0];\
# [video_faded_out2]trim=start={trim_start},setpts=PTS-STARTPTS[v1];\
# [audio_combined_faded_out2]atrim=start={trim_start},asetpts=PTS-STARTPTS[a1];\
# [v0][a0][v1][a1]concat=n=2:v=1:a=1[v_almost_final][a];\
# [v_almost_final]scale=2560:trunc(ow/a/2)*2:flags=bicubic[v]"

# '[0]fade=duration=2.5:start_time=37.02:type=out[s0];[s0]split=2[s1][s2];[s1]trim=end=3.1[s3];[s3]setpts=PTS-STARTPTS[s4];[1]volume=volume=0.6[s5];[2]adelay=6566.666666666667|6566.666666666667[s6];[s5][s6]amix=duration=first:inputs=2[s7];[s7]afade=duration=2.5:start_time=37.02:type=out[s8];[s8]asplit=2[s9][s10];[s9]atrim=end=3.1[s11];[s11]asetpts=PTS-STARTPTS[s12];[s2]trim=start=6.566666666666666[s13];[s13]setpts=PTS-STARTPTS[s14];[s10]atrim=start=6.566666666666666[s15];[s15]asetpts=PTS-STARTPTS[s16];[s4][s12][s14][s16]concat=a=1:n=2:v=1[s17];[s17]split=2[s18][s19];[s19]scale=854:trunc(ow/a/2)*2:flags=bicubic[s20]', 

def encode_video(output_video_filename, ffmpeg_filename, ffprobe_filename, dolphin_resolution, music_option, timeline_settings):
    encoder = Encoder(ffmpeg_filename, ffprobe_filename, dolphin_resolution, music_option, timeline_settings)
    encoder.encode(output_video_filename)

def test_generated_command():
    # output_format, crf, h26x_preset, video_codec, audio_codec, audio_bitrate, output_width, pix_fmt
    # , CrfEncodeSettings, SizeBasedEncodeSettings
    # SizeBasedEncodeSettings(output_format, video_codec, audio_codec, audio_bitrate, encode_size, output_width, pix_fmt)
    MODE = 0
    if MODE == 0:
        crf_encode_settings = CrfEncodeSettings("mkv", 18, "medium", "libx264", "libopus", "128k", 854, "yuv420p", True, 0.6, 1.0)
        timeline_settings = FromTTGhostSelectionTimelineSettings(crf_encode_settings, InputDisplay(INPUT_DISPLAY_CLASSIC, True))
        music_option = MusicOption(MUSIC_CUSTOM_MUSIC, "bubble_bath_the_green_orbs.wav")
        encoder = Encoder("ffmpeg", "ffprobe", "480p", music_option, timeline_settings, print_cmd=True)
        encoder.encode("test_crf_command.mkv")
    elif MODE == 1:
        #size_based_encode_settings = SizeBasedEncodeSettings("webm", "libvpx-vp9", "libopus", "64k", 52428800, None, "yuv420p")
        size_based_encode_settings = SizeBasedEncodeSettings("mp4", "libx264", "libopus", "64k", 52428800, None, "yuv420p", 0.6, 1.0)
        timeline_settings = FromTTGhostSelectionTimelineSettings(size_based_encode_settings)
        music_option = MusicOption(MUSIC_CUSTOM_MUSIC, "bubble_bath_the_green_orbs.wav")
        encoder = Encoder("ffmpeg", "ffprobe", "480p", music_option, timeline_settings, print_cmd=False)
        encoder.encode("test_size_based_command.mp4")
    elif MODE == 2:
        crf_encode_settings = CrfEncodeSettings("mkv", 18, "medium", "libx264", "libopus", "128k", None, "yuv420p", True, 0.6, 1.0)
        timeline_settings = FromTTGhostSelectionTimelineSettings(crf_encode_settings)
        music_option = MusicOption(MUSIC_GAME_BGM)
        encoder = Encoder("ffmpeg", "ffprobe", "480p", music_option, timeline_settings, print_cmd=False)
        encoder.encode("test_game_bgm_crf.mkv")

if __name__ == "__main__":
    test_generated_command()
