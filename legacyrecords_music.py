import legacyrecords_staticconfig
import requests
import csv
import pathlib

music_info_fieldnames = ("link", "source", "artist", "name")

class MusicInfo:
    __slots__ = music_info_fieldnames + ("music_filename",)

    def __init__(self, link, source, artist, name):
        self.link = link
        self.source = source
        self.artist = artist
        self.name = name
        self.music_filename = None

    def set_music_filename(self, music_filename):
        self.music_filename = music_filename

    def __repr__(self):
        return f"link: {self.link}, source: {self.source}, artist: {self.artist}, name: {self.name}, music_filename: {music_filename}"

def get_music(yt_recorder_config, mock_music_list_text=None):
    music_list_link = legacyrecords_staticconfig.music_list_link
    music_index = yt_recorder_config["music_index"]

    if mock_music_list_text is None:
        r = requests.get(music_list_link)
        if r.status_code != 200:
            raise RuntimeError(f"music_list_link returned {r.status_code}: {r.reason}")
        response_text = r.text
    else:
        response_text = mock_music_list_text
    response_text = response_text.strip()

    music_list = response_text.splitlines()
    if music_index >= len(music_list):
        return None

    music_info_str = music_list[music_index]
    music_info_str_iter = [music_info_str]

    reader = csv.DictReader(music_info_str_iter, fieldnames=music_info_fieldnames, delimiter=",", quotechar='"')
    for row in reader:
        music_info = MusicInfo(row["link"], row["source"], row["artist"], row["name"])
        break

    downloaded_music_filename = pathlib.Path(music_info.link).name
    downloaded_music_filepath = pathlib.Path(f"music_cached/{downloaded_music_filename}")

    if not downloaded_music_filepath.is_file():
        r = requests.get(music_info.link, allow_redirects=True)
        #if r.headers["content-type"] != "application/octet-stream":
        #    raise RuntimeError(f"Downloaded music file {music_info.link} is not binary!")

        downloaded_music_filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(downloaded_music_filepath, 'wb+') as f:
            f.write(r.content)

    music_info.set_music_filename(downloaded_music_filename)
    return music_info

def test_get_music():
    mock_music_list_text ="""\
https://cdn.discordapp.com/attachments/528745839708078093/932354387983097927/undertale_last_breath_phase_3.opus,https://www.youtube.com/watch?v=dIWNltBsq10,Benlab,Undertale Last Breath: An Enigmatic Encounter (Phase 3)
https://cdn.discordapp.com/attachments/528745839708078093/932356305929240706/-_Dark_Sheep-bYCbm469Zq0.webm,https://youtu.be/bYCbm469Zq0,Chroma,Dark Sheep
"""

    music_info = get_music({"music_index": 0}, mock_music_list_text)
    print(f"music_info: {music_info}")

def main():
    MODE = 0
    if MODE == 0:
        test_get_music()
    else:
        print("No mode selected!")

if __name__ == "__main__":
    main()
