import legacyrecords_staticconfig
import requests
import csv
import pathlib
import json
import subprocess
import re

music_info_fieldnames = ("link", "suggestor", "source", "artist", "name")

class MusicInfo:
    __slots__ = music_info_fieldnames + ("music_filename",)

    def __init__(self, link, suggestor, source, artist, name):
        self.link = link
        self.suggestor = suggestor
        self.source = source
        self.artist = artist
        self.name = name
        self.music_filename = None

    def download_if_not_exists_then_set_music_filename(self):
        downloaded_music_filename = pathlib.Path(self.link).name
        downloaded_music_filepath = pathlib.Path(f"music_cached/{downloaded_music_filename}")
    
        if not downloaded_music_filepath.is_file():
            r = requests.get(self.link, allow_redirects=True)
            #if r.headers["content-type"] != "application/octet-stream":
            #    raise RuntimeError(f"Downloaded music file {music_info.link} is not binary!")

            downloaded_music_filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(downloaded_music_filepath, 'wb+') as f:
                f.write(r.content)

        self.set_music_filename(str(downloaded_music_filepath))

    def set_music_filename(self, music_filename):
        self.music_filename = music_filename

    def __repr__(self):
        return f"link: {self.link}, suggestor: {self.suggestor}, source: {self.source}, artist: {self.artist}, name: {self.name}, music_filename: {self.music_filename}"

saved_music_durations_filepath = pathlib.Path("music_cached/music_durations.json")
audio_len_regex = re.compile(r"^size=N/A time=([0-9]{2}):([0-9]{2}):([0-9]{2}\.[0-9]{2})", flags=re.MULTILINE)

def get_audio_len(audio_filename):
    #print(f"audio_filename: {audio_filename}")
    ffmpeg_output = subprocess.check_output(["ffmpeg", "-i", audio_filename, "-f", "null", "-"], stderr=subprocess.STDOUT).replace(b"\r", b"\n").decode("utf-8")

    audio_len_match_objs = audio_len_regex.findall(ffmpeg_output)
    if len(audio_len_match_objs) == 0:
        raise RuntimeError(f"FFmpeg command did not return {audio_filename} audio duration!")

    audio_len_match_obj = audio_len_match_objs[-1]

    #print(f"audio_len_match_obj.group(0): {audio_len_match_obj}")
    audio_len_hours = int(audio_len_match_obj[0])
    audio_len_minutes = int(audio_len_match_obj[1])
    audio_len_seconds = float(audio_len_match_obj[2])
    #print(f"{audio_len_hours}:{audio_len_minutes}:{audio_len_seconds}")
    audio_len = audio_len_hours * 3600 + audio_len_minutes * 60 + audio_len_seconds
    return audio_len

class MusicFetcher:
    __slots__ = ("music_info_list",)

    def __init__(self, mock_music_list_text=None):
        if not saved_music_durations_filepath.is_file():
            with open(saved_music_durations_filepath, "w+") as f:
                json.dump({}, f, indent=2)

        self.get_music_info_list(mock_music_list_text)

    def get_music_info_list(self, mock_music_list_text=None):
        if mock_music_list_text is None:
            music_list_link = legacyrecords_staticconfig.music_list_link
            r = requests.get(music_list_link)
            if r.status_code != 200:
                raise RuntimeError(f"music_list_link returned {r.status_code}: {r.reason}")
            response_text = r.text
        else:
            response_text = mock_music_list_text
        response_text = response_text.strip()

        music_info_strs = response_text.splitlines()
        reader = csv.DictReader(music_info_strs, fieldnames=music_info_fieldnames, delimiter=",", quotechar='"')
        self.music_info_list = []
        for row in reader:
            music_info = MusicInfo(row["link"], row["suggestor"], row["source"], row["artist"], row["name"])
            self.music_info_list.append(music_info)

    def get_music_exceeding_duration(self, yt_recorder_config, approx_video_duration):
        all_music_indices = set(range(len(self.music_info_list)))        
        used_music_indices = set(yt_recorder_config["used_music_indices"])
        unused_music_indices = all_music_indices - used_music_indices
        if len(unused_music_indices) == 0:        
            return None, -1

        unused_music_indices_as_list = list(unused_music_indices)
        unused_music_indices_as_list.sort()

        with open(saved_music_durations_filepath, "r") as f:
            saved_music_durations = json.load(f)

        chosen_music_index = None
        chosen_music_info = None

        for music_index in unused_music_indices_as_list:
            music_info = self.music_info_list[music_index]
            music_info.download_if_not_exists_then_set_music_filename()

            music_duration = saved_music_durations.get(music_info.link)
            if music_duration is None:
                music_duration = get_audio_len(music_info.music_filename)
                saved_music_durations[music_info.link] = music_duration
            print(f"music_duration: {music_duration}")

            if music_duration >= approx_video_duration:
                chosen_music_index = music_index
                chosen_music_info = music_info
                break

        with open(saved_music_durations_filepath, "w+") as f:
            json.dump(saved_music_durations, f, indent=2)

        if chosen_music_index is not None:
            return chosen_music_info, chosen_music_index
        else:
            return None, -1

def test_get_music():
    mock_music_list_text ="""\
https://cdn.discordapp.com/attachments/528745839708078093/932354387983097927/undertale_last_breath_phase_3.opus,luckytyphlosion,https://www.youtube.com/watch?v=dIWNltBsq10,Benlab,Undertale Last Breath: An Enigmatic Encounter (Phase 3)
https://cdn.discordapp.com/attachments/528745839708078093/932356305929240706/-_Dark_Sheep-bYCbm469Zq0.webm,luckytyphlosion,https://youtu.be/bYCbm469Zq0,Chroma,Dark Sheep
"""

    music_fetcher = MusicFetcher(mock_music_list_text)
    music_info, music_index = music_fetcher.get_music_exceeding_duration({"used_music_indices": []}, 60)
    print(f"music_info: {music_info}, music_index: {music_index}")

    music_info, music_index = music_fetcher.get_music_exceeding_duration({"used_music_indices": []}, 60 * 4 + 1)
    print(f"music_info: {music_info}, music_index: {music_index}")

    music_info, music_index = music_fetcher.get_music_exceeding_duration({"used_music_indices": [0, 1]}, 0)
    print(f"music_info: {music_info}, music_index: {music_index}")

    music_info, music_index = music_fetcher.get_music_exceeding_duration({"used_music_indices": []}, 1000)
    print(f"music_info: {music_info}, music_index: {music_index}")

def main():
    MODE = 0
    if MODE == 0:
        test_get_music()
    else:
        print("No mode selected!")

if __name__ == "__main__":
    main()
