import legacyrecords_staticconfig
import requests
import csv
import pathlib
import json
import subprocess
import re

music_info_fieldnames = ("link", "suggestor", "source", "artist", "name", "ghost_id")

class MusicInfo:
    __slots__ = music_info_fieldnames + ("music_filename",)

    def __init__(self, link, suggestor, source, artist, name, ghost_id):
        self.link = link
        self.suggestor = suggestor
        self.source = source
        self.artist = artist
        self.name = name
        self.ghost_id = ghost_id
        self.music_filename = None

    def download_if_not_exists_then_set_music_filename(self):
        downloaded_music_filename = pathlib.Path(self.link).name
        downloaded_music_filepath = pathlib.Path(f"music_cached/{downloaded_music_filename}")
        # nondownloaded_music_filepath = pathlib.Path(f"music_cached/{self.link}")

        if not downloaded_music_filepath.is_file():
            if not self.link.startswith("http"):
                raise RuntimeError(f"Music file {self.link} does not exist and is not a link!")

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
audio_len_regex = re.compile(r"size=N/A time=([0-9]{2}):([0-9]{2}):([0-9]{2}\.[0-9]{2})", flags=re.MULTILINE)

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
    __slots__ = ("music_info_dict", "reserved_music_infos")

    def __init__(self, mock_music_list_text=None):
        if not saved_music_durations_filepath.is_file():
            saved_music_durations_filepath.parent.mkdir(parents=True, exist_ok=True)
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
        self.music_info_dict = {}
        self.reserved_music_infos = {}
        for row in reader:
            row_ghost_id = row.get("ghost_id")
            if row_ghost_id is not None:
                if len(row_ghost_id) != 40:
                    invalid_ghost_id = True
                else:
                    try:
                        int(row_ghost_id, 16)
                        invalid_ghost_id = False
                    except ValueError:
                        invalid_ghost_id = True
    
                if invalid_ghost_id:
                    raise RuntimeError(f"ghost_id {row_ghost_id} not valid!")

            row_link = row["link"]
            music_info = MusicInfo(row_link, row["suggestor"], row["source"], row["artist"], row["name"], row_ghost_id)
            self.music_info_dict[row_link] = music_info
            if row_ghost_id is not None:
                self.reserved_music_infos[row_ghost_id] = music_info

    def transition_to_used_music_links(self, yt_recorder_config):
        if yt_recorder_config["transitioned_to_used_music_links"]:
            return

        used_music_indices = set(yt_recorder_config["used_music_indices"])
        used_music_links = []
        #print(self.music_info_dict)
        for i, music_info_link in enumerate(self.music_info_dict.keys()):
            if i in used_music_indices:
                used_music_links.append(music_info_link)

        del yt_recorder_config["used_music_indices"]
        yt_recorder_config["used_music_links"] = used_music_links
        yt_recorder_config["transitioned_to_used_music_links"] = True

    def get_music_exceeding_duration(self, yt_recorder_config, approx_video_duration, ghost_id):
        all_music_links = set(self.music_info_dict.keys())
        used_music_links = set(yt_recorder_config["used_music_links"])
        unused_music_links = all_music_links - used_music_links
        if len(unused_music_links) == 0:        
            return None, -1

        chosen_music_link = None
        chosen_music_info = None

        reserved_music_info = self.reserved_music_infos.get(ghost_id)
        if reserved_music_info is not None:
            reserved_music_info.download_if_not_exists_then_set_music_filename()

            chosen_music_link = reserved_music_info.link
            chosen_music_info = reserved_music_info
        else:
            unused_music_links_as_list = list(unused_music_links)
            music_info_dict_keys_to_index = {music_info_link: i for i, music_info_link in enumerate(self.music_info_dict.keys())}
            unused_music_links_as_list.sort(key=lambda x: music_info_dict_keys_to_index[x])

            with open(saved_music_durations_filepath, "r") as f:
                saved_music_durations = json.load(f)

            for music_link in unused_music_links_as_list:
                music_info = self.music_info_dict[music_link]
                music_info.download_if_not_exists_then_set_music_filename()
                if music_info.ghost_id in self.reserved_music_infos:
                    continue

                music_duration = saved_music_durations.get(music_info.link)
                if music_duration is None:
                    music_duration = get_audio_len(music_info.music_filename)
                    saved_music_durations[music_info.link] = music_duration
                print(f"music_duration: {music_duration}")
    
                if music_duration >= approx_video_duration:
                    chosen_music_link = music_link
                    chosen_music_info = music_info
                    break

            with open(saved_music_durations_filepath, "w+") as f:
                json.dump(saved_music_durations, f, indent=2)

        if chosen_music_link is not None:
            return chosen_music_info, chosen_music_link
        else:
            return None, None

def test_get_music():
    mock_music_list_text ="""\
https://cdn.discordapp.com/attachments/528745839708078093/932354387983097927/undertale_last_breath_phase_3.opus,luckytyphlosion,https://www.youtube.com/watch?v=dIWNltBsq10,Benlab,Undertale Last Breath: An Enigmatic Encounter (Phase 3)
https://cdn.discordapp.com/attachments/528745839708078093/932356305929240706/-_Dark_Sheep-bYCbm469Zq0.webm,luckytyphlosion,https://youtu.be/bYCbm469Zq0,Chroma,Dark Sheep
Digimon World 3 Soundtrack - Protocol Ruins Extended-7FSqNAxoLYs.webm,luckytyphlosion,https://www.youtube.com/watch?v=7FSqNAxoLYs,Digimon World 3,Protocol Ruins,9A26652912090900D53CC19A18A1F656C5DD2FB5
"""

    music_fetcher = MusicFetcher(mock_music_list_text)
    music_info, music_index = music_fetcher.get_music_exceeding_duration({"used_music_links": []}, 60)
    print(f"music_info: {music_info}, music_index: {music_index}")

    music_info, music_index = music_fetcher.get_music_exceeding_duration({"used_music_links": []}, 60 * 4 + 1)
    print(f"music_info: {music_info}, music_index: {music_index}")

    music_info, music_index = music_fetcher.get_music_exceeding_duration({"used_music_links": [0, 1]}, 0)
    print(f"music_info: {music_info}, music_index: {music_index}")

    music_info, music_index = music_fetcher.get_music_exceeding_duration({"used_music_links": []}, 1000)
    print(f"music_info: {music_info}, music_index: {music_index}")

def validate_music_list():
    MusicFetcher()

def test_music_fetcher_transition_to_links_reserved_music_infos():
    import find_ghost_to_record

    with open("music_fetcher_test.dump", "r") as f:
        mock_music_list_text = f.read()

    music_fetcher = MusicFetcher(mock_music_list_text)
    yt_recorder_config = find_ghost_to_record.read_in_recorder_config()
    music_fetcher.transition_to_used_music_links(yt_recorder_config)
    find_ghost_to_record.update_recorder_config_state_and_serialize(yt_recorder_config, 0, "yt_recorder_config_legacy_records_transition_out.json")

    print('500, "FC3F7F2043336671D84087ACD8F50DFF93F6A4C5"')
    music_info, music_link = music_fetcher.get_music_exceeding_duration(yt_recorder_config, 500, "FC3F7F2043336671D84087ACD8F50DFF93F6A4C5")
    print(f"music_info: {music_info}, music_link: {music_link}\n")

    print('500, "9A26652912090900D53CC19A18A1F656C5DD2FB5"')
    music_info, music_link = music_fetcher.get_music_exceeding_duration(yt_recorder_config, 500, "9A26652912090900D53CC19A18A1F656C5DD2FB5")
    print(f"music_info: {music_info}, music_link: {music_link}\n")

    print('120, "9A26652912090900D53CC19A18A1F656C5DD2FB5"')
    music_info, music_link = music_fetcher.get_music_exceeding_duration(yt_recorder_config, 120, "9A26652912090900D53CC19A18A1F656C5DD2FB5")
    print(f"music_info: {music_info}, music_link: {music_link}\n")

    print('120, "FC3F7F2043336671D84087ACD8F50DFF93F6A4C5"')
    music_info, music_link = music_fetcher.get_music_exceeding_duration(yt_recorder_config, 120, "FC3F7F2043336671D84087ACD8F50DFF93F6A4C5")
    print(f"music_info: {music_info}, music_link: {music_link}\n")

def main():
    MODE = 1
    if MODE == 0:
        test_get_music()
    elif MODE == 1:
        validate_music_list()
    elif MODE == 2:
        test_music_fetcher_transition_to_links_reserved_music_infos()
    else:
        print("No mode selected!")

if __name__ == "__main__":
    main()
