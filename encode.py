import subprocess
import ffmpeg
import os
import re
import pathlib

from stateclasses.timeline_classes import *
from stateclasses.encode_classes import *
from stateclasses.music_option_classes import *

audio_len_regex = re.compile(r"^size=N/A time=([0-9]{2}):([0-9]{2}):([0-9]{2}\.[0-9]{2})", flags=re.MULTILINE)

dev_null = "/dev/null" if os.name == "posix" else "NUL"

class DynamicFilterArgs:
    __slots__ = ("adelay_value", "fade_start_time", "trim_start")

    def __init__(self, adelay_value, fade_start_time, trim_start):
        self.adelay_value = adelay_value
        self.fade_start_time = fade_start_time
        self.trim_start = trim_start

FROM_TT_GHOST_SELECT_TRACK_LOADING_BLACK_SCREEN_TIMESTAMP = 3.1

class Encoder:
    __slots__ = ("ffmpeg_filename", "dolphin_resolution", "music_option", "timeline_settings", "dump_audio_len", "print_cmd")

    def __init__(self, ffmpeg_filename, dolphin_resolution, music_option, timeline_settings, print_cmd=False):
        self.ffmpeg_filename = ffmpeg_filename
        self.dolphin_resolution = dolphin_resolution
        self.music_option = music_option
        self.timeline_settings = timeline_settings
        self.dump_audio_len = None
        self.print_cmd = print_cmd

    def get_dump_audio_len(self, audio_file="dolphin/User/Dump/Audio/dspdump.wav"):
        if self.dump_audio_len is not None:
            return self.dump_audio_len

        dspdump_ffmpeg_output = subprocess.check_output([self.ffmpeg_filename, "-i", audio_file, "-acodec", "copy", "-f", "null", "-"], stderr=subprocess.STDOUT).decode(encoding="ascii")
        audio_len_match_obj = audio_len_regex.search(dspdump_ffmpeg_output)
        if not audio_len_match_obj:
            raise RuntimeError("FFmpeg command did not return dspdump.wav audio duration!")
        audio_len_hours = int(audio_len_match_obj.group(1))
        audio_len_minutes = int(audio_len_match_obj.group(2))
        audio_len_seconds = float(audio_len_match_obj.group(3))
        audio_len = audio_len_hours * 3600 + audio_len_minutes * 60 + audio_len_seconds

        self.dump_audio_len = audio_len
        return audio_len

    def encode_stream_copy(self, output_video_filename):
        subprocess.run(
            (self.ffmpeg_filename, "-y", "-i", "dolphin/User/Dump/Frames/framedump0.avi", "-i", "dolphin/User/Dump/Audio/dspdump.wav", "-c", "copy", output_video_filename), check=True
        )

    def gen_dynamic_filter_args(self, fade_duration):
        output_params = {}
    
        with open("dolphin/output_params.txt", "r") as f:
            for line in f:
                if line.strip() == "":
                    continue
    
                param_name, param_value = line.split(": ", maxsplit=1)
                output_params[param_name] = param_value.strip()
    
        frame_replay_starts = int(output_params["frameReplayStarts"])
        frame_recording_starts = int(output_params["frameRecordingStarts"])
    
        adelay_value = ((frame_replay_starts - frame_recording_starts) * 1000)/60
        audio_len = self.get_dump_audio_len()
        fade_start_time = audio_len - fade_duration
        trim_start = (frame_replay_starts - frame_recording_starts)/60

        return DynamicFilterArgs(adelay_value, fade_start_time, trim_start)

    def encode_from_top_10_leaderboard(self):
        dolphin_resolution = self.dolphin_resolution
        music_option = self.music_option
        timeline_settings = self.timeline_settings

        encode_settings = timeline_settings.encode_settings
        fade_duration = encode_settings.fade_duration

        dynamic_filter_args = self.gen_dynamic_filter_args(fade_duration)

        top_10_video_in_file = ffmpeg.input("dolphin/User/Dump/Frames/top10.avi")
        top_10_audio_in_file = ffmpeg.input("dolphin/User/Dump/Audio/top10.wav")
        video_in_file = ffmpeg.input("dolphin/User/Dump/Frames/framedump0.avi")
        audio_in_file = ffmpeg.input("dolphin/User/Dump/Audio/dspdump.wav")

        if music_option.option == MUSIC_CUSTOM_MUSIC:
            music_in_file = ffmpeg.input(music_option.music_filename)
            game_volume_stream = ffmpeg.filter(audio_in_file, "volume", volume=encode_settings.game_volume)
            audio_combined_stream = ffmpeg.filter([game_volume_stream, music_in_file], "amix", inputs=2, duration="first")            
        else:
            audio_combined_stream = audio_in_file

        video_faded_stream = ffmpeg.filter(video_in_file, "fade", type="out", duration=fade_duration, start_time=dynamic_filter_args.fade_start_time)
    
        audio_combined_faded_stream = ffmpeg.filter(audio_combined_stream, "afade", type="out", duration=fade_duration, start_time=dynamic_filter_args.fade_start_time)
    
        all_streams = [
            top_10_video_in_file,
            top_10_audio_in_file,
            video_faded_stream,
            audio_combined_faded_stream
        ]

        almost_final_streams = ffmpeg.filter_multi_output(all_streams, "concat", n=2, v=1, a=1)
        if encode_settings.output_width is not None:
            final_video_stream = ffmpeg.filter(almost_final_streams[0], "scale", encode_settings.output_width, "trunc(ow/a/2)*2", flags="bicubic")
        else:
            final_video_stream = almost_final_streams[0]

        final_audio_stream = almost_final_streams[1]

        return final_video_stream, final_audio_stream

    def encode_from_tt_ghost_select(self):
        dolphin_resolution = self.dolphin_resolution
        music_option = self.music_option
        timeline_settings = self.timeline_settings

        encode_settings = timeline_settings.encode_settings
        fade_duration = encode_settings.fade_duration

        dynamic_filter_args = self.gen_dynamic_filter_args(fade_duration)

        video_in_file = ffmpeg.input("dolphin/User/Dump/Frames/framedump0.avi")
        audio_in_file = ffmpeg.input("dolphin/User/Dump/Audio/dspdump.wav")
        if music_option.option == MUSIC_CUSTOM_MUSIC:
            music_in_file = ffmpeg.input(music_option.music_filename)
            adelay_stream = ffmpeg.filter(music_in_file, "adelay", f"{dynamic_filter_args.adelay_value}|{dynamic_filter_args.adelay_value}")
            game_volume_stream = ffmpeg.filter(audio_in_file, "volume", volume=encode_settings.game_volume)
            audio_combined_stream = ffmpeg.filter([game_volume_stream, adelay_stream], "amix", inputs=2, duration="first")            
        else:
            audio_combined_stream = audio_in_file

        video_faded_stream = ffmpeg.filter(video_in_file, "fade", type="out", duration=fade_duration, start_time=dynamic_filter_args.fade_start_time).split()
    
        audio_combined_faded_stream = ffmpeg.filter(audio_combined_stream, "afade", type="out", duration=fade_duration, start_time=dynamic_filter_args.fade_start_time).asplit()
    
        all_streams_trimmed = [
            ffmpeg.trim(video_faded_stream[0], end=FROM_TT_GHOST_SELECT_TRACK_LOADING_BLACK_SCREEN_TIMESTAMP).setpts("PTS-STARTPTS"),
            ffmpeg.filter(audio_combined_faded_stream[0], "atrim", end=FROM_TT_GHOST_SELECT_TRACK_LOADING_BLACK_SCREEN_TIMESTAMP).filter("asetpts", "PTS-STARTPTS"),
            ffmpeg.trim(video_faded_stream[1], start=dynamic_filter_args.trim_start).setpts("PTS-STARTPTS"),
            ffmpeg.filter(audio_combined_faded_stream[1], "atrim", start=dynamic_filter_args.trim_start).filter("asetpts", "PTS-STARTPTS")
        ]

        almost_final_streams = ffmpeg.filter_multi_output(all_streams_trimmed, "concat", n=2, v=1, a=1)
        if encode_settings.output_width is not None:
            final_video_stream = ffmpeg.filter(almost_final_streams[0], "scale", encode_settings.output_width, "trunc(ow/a/2)*2", flags="bicubic")
        else:
            final_video_stream = almost_final_streams[0]
    
        final_audio_stream = almost_final_streams[1]

        return final_video_stream, final_audio_stream

    def encode_complex(self, output_video_filename):
        dolphin_resolution = self.dolphin_resolution
        music_option = self.music_option
        timeline_settings = self.timeline_settings

        encode_settings = timeline_settings.encode_settings
        fade_duration = encode_settings.fade_duration

        if timeline_settings.type == TIMELINE_FROM_TT_GHOST_SELECTION:
            final_video_stream, final_audio_stream = self.encode_from_tt_ghost_select()
        elif timeline_settings.type == TIMELINE_FROM_TOP_10_LEADERBOARD:
            final_video_stream, final_audio_stream = self.encode_from_top_10_leaderboard()
        else:
            raise RuntimeError(f"Unknown timeline type \"{timeline_settings.type}\"!")

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
                
            output_stream = ffmpeg.output(final_video_stream, final_audio_stream, output_video_filename, **ffmpeg_output_kwargs)
            if self.print_cmd:
                command = ffmpeg.compile(output_stream, cmd=self.ffmpeg_filename, overwrite_output=True)
                print(f"command: {command}")
            else:
                ffmpeg.run(output_stream, cmd=self.ffmpeg_filename, overwrite_output=True)
        elif encode_settings.type == ENCODE_TYPE_SIZE_BASED:
            encode_size_bits = encode_settings.encode_size * 8
            run_len = self.get_dump_audio_len() - (dynamic_filter_args.trim_start - FROM_TT_GHOST_SELECT_TRACK_LOADING_BLACK_SCREEN_TIMESTAMP)
            print(f"run_len: {run_len}")
            if encode_settings.video_codec == "libx264":
                dampening_factor = 0.98
            else:
                dampening_factor = 0.99

            avg_video_bitrate = int(dampening_factor * (encode_size_bits/run_len - encode_settings.audio_bitrate))

            ffmpeg_output_kwargs = {
                "vcodec": encode_settings.video_codec,
                "video_bitrate": avg_video_bitrate,
                "pix_fmt": encode_settings.pix_fmt,                
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
            
            if self.print_cmd:
                pass1_command = ffmpeg.compile(output_stream_pass1, cmd=self.ffmpeg_filename, overwrite_output=True)
                pass2_command = ffmpeg.compile(output_stream_pass2, cmd=self.ffmpeg_filename, overwrite_output=True)

                print(f"pass1_command: {pass1_command}\npass2_command: {pass2_command}")
            else:
                ffmpeg.run(output_stream_pass1, cmd=self.ffmpeg_filename, overwrite_output=True)
                ffmpeg.run(output_stream_pass2, cmd=self.ffmpeg_filename, overwrite_output=True)
                if encode_settings.output_format == "mp4":
                    mkv_to_mp4_args = [self.ffmpeg_filename, "-y", "-i", tentative_output_video_filename, "-c", "copy"]
                    if encode_settings.audio_codec == "libopus":
                        mkv_to_mp4_args.extend(("-strict", "-2"))

                    # -strict -2 must be before output video
                    mkv_to_mp4_args.append(output_video_filename)

                    subprocess.run(mkv_to_mp4_args, check=True)
                    output_video_filepath_as_mkv.unlink(missing_ok=True)
        else:
            assert False

    def encode(self, output_video_filename):
        output_video_path = pathlib.Path(output_video_filename)
        output_video_path.parent.mkdir(parents=True, exist_ok=True)

        if self.timeline_settings.type == TIMELINE_NO_ENCODE:
            self.encode_stream_copy(output_video_filename)
        elif self.timeline_settings.type in (TIMELINE_FROM_TT_GHOST_SELECTION, TIMELINE_FROM_TOP_10_LEADERBOARD):
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

def encode_video(output_video_filename, ffmpeg_filename, dolphin_resolution, music_option, timeline_settings):
    encoder = Encoder(ffmpeg_filename, dolphin_resolution, music_option, timeline_settings)
    encoder.encode(output_video_filename)

def test_generated_command():
    # output_format, crf, h26x_preset, video_codec, audio_codec, audio_bitrate, output_width, pix_fmt
    # , CrfEncodeSettings, SizeBasedEncodeSettings
    # SizeBasedEncodeSettings(output_format, video_codec, audio_codec, audio_bitrate, encode_size, output_width, pix_fmt)
    MODE = 2
    if MODE == 0:
        crf_encode_settings = CrfEncodeSettings("mkv", 18, "medium", "libx264", "libopus", "128k", 854, "yuv420p")
        timeline_settings = FromTTGhostSelectionTimelineSettings(crf_encode_settings)
        music_option = MusicOption(MUSIC_CUSTOM_MUSIC, "bubble_bath_the_green_orbs.wav")
        encoder = Encoder("ffmpeg", "480p", music_option, timeline_settings, print_cmd=True)
        encoder.encode("test_crf_command.mkv")
    elif MODE == 1:
        #size_based_encode_settings = SizeBasedEncodeSettings("webm", "libvpx-vp9", "libopus", "64k", 52428800, None, "yuv420p")
        size_based_encode_settings = SizeBasedEncodeSettings("mp4", "libx264", "libopus", "64k", 52428800, None, "yuv420p")
        timeline_settings = FromTTGhostSelectionTimelineSettings(size_based_encode_settings)
        music_option = MusicOption(MUSIC_CUSTOM_MUSIC, "bubble_bath_the_green_orbs.wav")
        encoder = Encoder("ffmpeg", "480p", music_option, timeline_settings, print_cmd=False)
        encoder.encode("test_size_based_command.mp4")
    elif MODE == 2:
        crf_encode_settings = CrfEncodeSettings("mkv", 18, "medium", "libx264", "libopus", "128k", None, "yuv420p")
        timeline_settings = FromTTGhostSelectionTimelineSettings(crf_encode_settings)
        music_option = MusicOption(MUSIC_GAME_BGM)
        encoder = Encoder("ffmpeg", "480p", music_option, timeline_settings, print_cmd=False)
        encoder.encode("test_game_bgm_crf.mkv")

if __name__ == "__main__":
    test_generated_command()
