from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, HttpRequest
import google_auth_oauthlib.flow

import json
import urllib.parse
from datetime import datetime, timezone, timedelta
import dateutil.parser
import yaml
import pickle
import itertools
import pathlib
import find_ghost_to_record
import time
import identifiers

CTGP_TAGS = ["Mario Kart Wii","mkw","mkwii","mario kart","mario kart wii world records","mkw records","mkw world records","mkw bkt","mkw wr","ctgp records","wr","bkt","best known time","world record","CTGP","Wii"]

EU_TYPE_NONE = 0
EU_TYPE_TRACK = 1
EU_TYPE_VEHICLE = 2
EU_TYPE_BOTH = 3

TAGS_CHARACTER_LIMIT = 500

class AdditionalTagTemplate:
    __slots__ = ("tag", "eu_type")

    def __init__(self, tag, eu_type=EU_TYPE_NONE):
        self.tag = tag
        self.eu_type = eu_type

additional_tag_templates = (
    AdditionalTagTemplate("{track_eu}", EU_TYPE_TRACK),
    AdditionalTagTemplate("{vehicle_eu}", EU_TYPE_VEHICLE),
    AdditionalTagTemplate("{track} {vehicle} wr"),
    AdditionalTagTemplate("{track} {vehicle} bkt"),
    AdditionalTagTemplate("mario kart wii {track} {vehicle} wr"),
    AdditionalTagTemplate("mario kart wii {track} {vehicle} bkt"),
    AdditionalTagTemplate("{track} with {vehicle}"),
    AdditionalTagTemplate("mkw {track} {vehicle} wr"),
    AdditionalTagTemplate("mkw {track} {vehicle} bkt"),
    AdditionalTagTemplate("mkwii {track} {vehicle} wr"),
    AdditionalTagTemplate("mkwii {track} {vehicle} bkt"),
    AdditionalTagTemplate("{track_eu} {vehicle_eu} wr", EU_TYPE_BOTH),
    AdditionalTagTemplate("{track_eu} {vehicle_eu} bkt", EU_TYPE_BOTH)
)

scopes = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]

def get_channel_content_details(api):
    response = api.channels().list(
        part="contentDetails",
        maxResults=50,
        mine=True
    ).execute()

    return response

def get_channel_playlist_items(api, playlist_id, page_token=None):
    response = api.playlistItems().list(
        part="contentDetails",
        playlistId=playlist_id,
        maxResults=50,
        pageToken=page_token
    ).execute()
    return response

def slice_iterator(lst, slice_len):
    for i in range(0, len(lst), slice_len):
        yield lst[i:i + slice_len]

def chunked(it, size):
    it = iter(it)
    
    while True:
        p = tuple(itertools.islice(it, size))
        if not p:
            break
        yield p

def calc_tag_len(tag):
    if " " in tag:
        return len(tag) + 2
    else:
        return len(tag)

def calc_adding_tag_len(tag):
    return calc_tag_len(tag) + 1

def calc_tags_len(tags):
    total_tags_len = 0
    for tag in tags:
        total_tags_len += calc_tag_len(tag)

    total_tags_len += max(len(tags) - 1, 0)

    return total_tags_len

def add_additional_tags(initial_tags, additional_tag_templates, yt_update_info):
    video_tags = list(initial_tags)

    total_tags_len = calc_tags_len(video_tags)
    human_track_id = identifiers.track_id_to_human_track_id[yt_update_info["track_id"]]
    vehicle_id = yt_update_info["vehicle_id"]

    track_name = identifiers.track_names[human_track_id]
    track_name_eu = identifiers.track_names_eu.get(human_track_id)
    if track_name_eu is None:
        track_name_eu_exists = False
        track_name_eu = track_name
    else:
        track_name_eu_exists = True

    vehicle_name = identifiers.vehicle_names[vehicle_id]
    vehicle_name_eu = identifiers.vehicle_names_eu.get(vehicle_id)
    if vehicle_name_eu is None:
        vehicle_name_eu_exists = False
        vehicle_name_eu = track_name
    else:
        vehicle_name_eu_exists = True

    format_mapping = {
        "track_eu": track_name_eu,
        "track": track_name,
        "vehicle_eu": vehicle_name_eu,
        "vehicle": vehicle_name
    }
        
    # try to stuff as many additional tags as possible
    for additional_tag_template in additional_tag_templates:
        eu_type = additional_tag_template.eu_type
        tag_sensible = True

        #if eu_type == EU_TYPE_NONE:
        #    track_name_eu_exists = True
        if eu_type == EU_TYPE_TRACK:
            if not track_name_eu_exists:
                tag_sensible = False
        elif eu_type == EU_TYPE_VEHICLE:
            if not vehicle_name_eu_exists:
                tag_sensible = False
        elif eu_type == EU_TYPE_BOTH:
            if not track_name_eu_exists and not vehicle_name_eu_exists:
                tag_sensible = False

        if not tag_sensible:
            continue

        additional_tag = additional_tag_template.tag.format_map(format_mapping)
        additional_tag_len = calc_adding_tag_len(additional_tag)
        if total_tags_len + additional_tag_len > TAGS_CHARACTER_LIMIT:
            break
        else:
            total_tags_len += additional_tag_len
            video_tags.append(additional_tag)

    return video_tags

def tags_to_str(tags):
    output = ",".join(f'"{tag}"' if " " in tag else tag for tag in tags)
    return output

class VideoInfo:
    __slots__ = ("video_id", "title")

    def __init__(self, video_id):
        self.video_id = video_id

def sleep_by_walltime(seconds, sleep_time=5):
    wait_until_datetime = datetime.now(tz=timezone.utc) + timedelta(seconds=seconds)
    while datetime.now(tz=timezone.utc) < wait_until_datetime:
        time.sleep(sleep_time)

def update_title_description_and_schedule(yt_recorder_config):
    with open("credentials.yml", "r") as f:
        credentials = yaml.safe_load(f)

    yt_update_infos = find_ghost_to_record.read_yt_update_infos()

    uploaded_videos_playlist_id = credentials["uploaded_videos_playlist_id"]

    read_credentials_from_file = True

    if not read_credentials_from_file:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        "client_secrets.json", scopes)

        authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')

        yt_credentials = flow.run_console()
        with open("yt_credentials.pickle", "wb+") as f:
            pickle.dump(yt_credentials, f, protocol=pickle.HIGHEST_PROTOCOL)
    else:
        with open("yt_credentials.pickle", "rb") as f:
            yt_credentials = pickle.load(f)

    video_infos = {}

    with build("youtube", "v3", credentials=yt_credentials) as api:
        while True:
            page_token = None
            print("INFO: Getting uploaded video IDs!")
            while True:
                response = get_channel_playlist_items(api, uploaded_videos_playlist_id, page_token)
                video_infos.update(
                    {video_id: VideoInfo(video_id) for video_id in (item["contentDetails"]["videoId"] for item in response["items"])}
                )
                next_page_token = response.get("nextPageToken")
                if next_page_token is None:
                    break
                page_token = next_page_token

            print("INFO: Getting uploaded video titles!")

            for i, video_infos_part in enumerate(chunked(video_infos.values(), 50)):
                video_ids_str = ",".join(video_info.video_id for video_info in video_infos_part)
                #output += f"video_ids_str: {video_ids_str}\n"
                videos = api.videos().list(
                    id=video_ids_str,
                    part="snippet"
                ).execute()
    
                for video in videos["items"]:
                    video_infos[video["id"]].title = video["snippet"]["title"]

            print("INFO: Setting video title/description/etc.!")

            output = ""
            for video_id, video_info in video_infos.items():
                yt_update_info = yt_update_infos.get(video_info.title)
                if yt_update_info is not None:
                    print(f"Found video to update! video title: {yt_update_info['yt_title']}")
                    initial_tags = CTGP_TAGS
                    video_tags = add_additional_tags(initial_tags, additional_tag_templates, yt_update_info)
                    response = api.videos().update(
                        part="snippet,id,status",
                        body={
                            "snippet": {
                                "title": yt_update_info["yt_title"],
                                "categoryId": "20",
                                "description": yt_update_info["yt_description"],
                                "tags": video_tags,
                            },
                            "status": {
                                "selfDeclaredMadeForKids": False,
                                "privacyStatus": "private",
                                "publishAt": yt_update_info["schedule_datetime_str"]
                            },
                            "id": video_id
                        }
                    ).execute()
    
                    del yt_update_infos[video_info.title]
                    find_ghost_to_record.serialize_yt_update_infos(yt_update_infos)
    
            if len(yt_update_infos) == 0:
                break

            sleep_by_walltime(10*60)

    find_ghost_to_record.update_recorder_config_state_and_serialize(yt_recorder_config, find_ghost_to_record.SETTING_NUM_REMAINING_GHOSTS)

def get_uploaded_videos_playlist_id():
    read_credentials_from_file = True

    if not read_credentials_from_file:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        "client_secrets.json", scopes)

        authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')

        yt_credentials = flow.run_console()
        with open("yt_credentials.pickle", "wb+") as f:
            pickle.dump(yt_credentials, f, protocol=pickle.HIGHEST_PROTOCOL)
    else:
        with open("yt_credentials.pickle", "rb") as f:
            yt_credentials = pickle.load(f)

    with build("youtube", "v3", credentials=yt_credentials) as api:
        response = get_channel_content_details(api)

    uploaded_videos_playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    credentials_path = pathlib.Path("credentials.yml")
    if not credentials_path.is_file():
        credentials = {}
    else:
        with open(credentials_path, "r") as f:
            credentials = yaml.safe_load(f)

    credentials["uploaded_videos_playlist_id"] = uploaded_videos_playlist_id

    with open(credentials_path, "w+") as f:
        yaml.dump(credentials, f)

def test_add_additional_tags():
    yt_update_info = {
        "track_id": 6,
        "vehicle_id": 0x20
    }
    initial_tags = CTGP_TAGS
    video_tags = add_additional_tags(CTGP_TAGS, additional_tag_templates, yt_update_info)
    video_tags_as_str = tags_to_str(video_tags)
    print(f"video_tags: {video_tags}\n\nvideo_tags as str: {video_tags_as_str}\n\ntags len: {len(video_tags_as_str)}")

def main():
    MODE = 1
    if MODE == 0:
        get_uploaded_videos_playlist_id()
    elif MODE == 1:
        test_add_additional_tags()
    else:
        print("No mode selected!")

if __name__ == "__main__":
    main()
