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

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, HttpRequest
import google_auth_oauthlib.flow
import google.auth.exceptions
import google.auth.transport.requests
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
import inspect

import description

CTGP_TAGS = ["Mario Kart Wii","mkw","mkwii","mario kart","mario kart wii world records","mkw records","mkw world records","mkw bkt","mkw wr","ctgp records","wr","bkt","best known time","world record","CTGP","Wii","CTs","CT","Custom Track","Custom Tracks"]

TAG_TYPE_NONE = 0
TAG_TYPE_VEHICLE = 1

TAGS_CHARACTER_LIMIT = 500

class AdditionalTagTemplate:
    __slots__ = ("tag",)

    def __init__(self, tag):
        self.tag = tag

# bike wr
# kart wr
# bike bkt
# kart bkt
# custom track name
# name vehicle bkt
# name vehicle wr
# 

has_vehicle_modifier_additional_tag_templates = (
    AdditionalTagTemplate("{track}"),
    AdditionalTagTemplate("{vehicle_modifier}"),
    AdditionalTagTemplate("{track} {vehicle_modifier} wr"),
    AdditionalTagTemplate("{track} {vehicle_modifier} bkt"),
    AdditionalTagTemplate("{vehicle_modifier} wr"),
    AdditionalTagTemplate("{vehicle_modifier} bkt"),
    AdditionalTagTemplate("mario kart wii {track} {vehicle_modifier} wr"),
    AdditionalTagTemplate("mario kart wii {track} {vehicle_modifier} bkt"),
    AdditionalTagTemplate("{track} with {vehicle_modifier}"),
    AdditionalTagTemplate("mkw {track} {vehicle_modifier} wr"),
    AdditionalTagTemplate("mkw {track} {vehicle_modifier} bkt"),
    AdditionalTagTemplate("mkwii {track} {vehicle_modifier} wr"),
    AdditionalTagTemplate("mkwii {track} {vehicle_modifier} bkt"),
)

no_vehicle_modifier_additional_tag_templates = ( 
    AdditionalTagTemplate("{track}"),
    AdditionalTagTemplate("{track} wr"),
    AdditionalTagTemplate("{track} bkt"),
    AdditionalTagTemplate("mario kart wii {track} wr"),
    AdditionalTagTemplate("mario kart wii {track} bkt"),
    AdditionalTagTemplate("mkw {track} wr"),
    AdditionalTagTemplate("mkw {track} bkt"),
    AdditionalTagTemplate("mkwii {track} wr"),
    AdditionalTagTemplate("mkwii {track} bkt"),
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

def add_additional_tags_no_preparation(additional_tag_templates, format_mapping, video_tags, total_tags_len):
    # try to stuff as many additional tags as possible
    hit_tag_limit = False

    for additional_tag_template in additional_tag_templates:
        additional_tag = additional_tag_template.tag.format_map(format_mapping)
        additional_tag_len = calc_adding_tag_len(additional_tag)
        if total_tags_len + additional_tag_len > TAGS_CHARACTER_LIMIT:
            hit_tag_limit = True
            break
        else:
            total_tags_len += additional_tag_len
            video_tags.append(additional_tag)

    return hit_tag_limit, total_tags_len

def add_additional_tags(initial_tags, yt_update_info):
    has_vehicle_modifier_additional_tag_templates
    no_vehicle_modifier_additional_tag_templates
    video_tags = list(initial_tags)

    total_tags_len = calc_tags_len(video_tags)
    track_name = yt_update_info["track_name"]
    version = yt_update_info["version"]
    vehicle_modifier = yt_update_info["vehicle_modifier"]
    
    if vehicle_modifier is not None:
        additional_tag_templates = has_vehicle_modifier_additional_tag_templates
        format_mapping = {
            "track": track_name,
            "vehicle_modifier": vehicle_modifier
        }
    else:
        additional_tag_templates = no_vehicle_modifier_additional_tag_templates
        format_mapping = {
            "track": track_name
        }

    hit_tag_limit, total_tags_len = add_additional_tags_no_preparation(additional_tag_templates, format_mapping, video_tags, total_tags_len)

    if not hit_tag_limit and version is not None:
        track_name_and_version = description.create_track_name_and_version(track_name, version)
        format_mapping["track"] = track_name_and_version
        add_additional_tags_no_preparation(additional_tag_templates, format_mapping, video_tags, total_tags_len)

    return video_tags

def tags_to_str(tags):
    output = ",".join(f'"{tag}"' if " " in tag else tag for tag in tags)
    return output

class VideoInfo:
    __slots__ = ("video_id", "title", "upload_status", "processing_details")

    def __init__(self, video_id):
        self.video_id = video_id
        self.title = None
        self.upload_status = None
        self.processing_details = None

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

    credentials_filepath = pathlib.Path("yt_credentials.pickle")
    get_credentials_from_api = False

    if credentials_filepath.is_file():
        with open("yt_credentials.pickle", "rb") as f:
            yt_credentials = pickle.load(f)
        #print(f"inspect.findsource(yt_credentials.refresh): {''.join(inspect.findsource(yt_credentials.refresh)[0])}")
        #print(f"inspect.getsourcefile(yt_credentials.refresh): {inspect.getsourcefile(yt_credentials.refresh)}")
        #print(f"inspect.getsourcefile(yt_credentials.refresh): {inspect.getsourcefile(yt_credentials.refresh)}")
        #print(f"type(yt_credentials).__name__: {type(yt_credentials).__name__}")
        request = google.auth.transport.requests.Request()
        try:
            yt_credentials.refresh(request)
            get_credentials_from_api = False
        except google.auth.exceptions.RefreshError:
            get_credentials_from_api = True

        print(f"yt_credentials.expired: {yt_credentials.expired}")
        # = yt_credentials.expired

    if get_credentials_from_api:
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
                    part="snippet,status,processingDetails"
                ).execute()

                for video in videos["items"]:
                    video_info = video_infos[video["id"]]
                    video_info.title = video["snippet"]["title"]
                    video_info.upload_status = video["status"]["uploadStatus"]
                    video_info.processing_details = video.get("processingDetails")
                    #if "Dry Dry Ruins" in video_info.title:
                    #    print(f"vipd: {video_info.processing_details}")

            print("INFO: Setting video title/description/etc.!")

            output = ""
            for video_id, video_info in video_infos.items():
                yt_update_info = yt_update_infos.get(video_info.title)
                if yt_update_info is not None:
                    print(f"video_info.upload_status: {video_info.upload_status}, video_info.processing_details: {video_info.processing_details}")

                    #if video_info.upload_status not in ("uploaded", "processed"):
                    #    
                    #elif video_info.upload_status in ("deleted", "failed", "rejected"):
                    #    raise RuntimeError(f"Upload was unsuccessful! upload_status: {video_info.upload_status}, title: {yt_update_info['yt_title']}")
                    #else:
                    #    continue

                    print(f"Found video to update! video title: {yt_update_info['yt_title']}")
                    initial_tags = CTGP_TAGS
                    video_tags = add_additional_tags(initial_tags, yt_update_info)
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
                                "publishAt": yt_update_info["schedule_datetime_str"],
                                "embeddable": True
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
    read_credentials_from_file = False

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
        "track_name": "Delfino Island",
        "version": "v3.1",
        "vehicle_modifier": "Kart"
    }
    initial_tags = CTGP_TAGS
    video_tags = add_additional_tags(CTGP_TAGS, yt_update_info)
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
