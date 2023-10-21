#!/usr/bin/env python3
import constants
from logger import youtube_logger
from auth import youtube_oauth
from datetime import datetime
import json, os, requests, subprocess, time

class youtube_api():
    """
        This class is designed to handle the searching for Channel IDs
        and Channel Names, searching for Videos from the configured Channels
        that match the configured titles, liking any videos that match
        the configuration, and downloading the videos for playback later
    """

    ########################
    ### PUBLIC CONSTANTS ###
    ########################
    BASE_URL = constants.DL_BASE_URL
    FORMAT = constants.VIDEO_FORMAT
    NAME = constants.VIDEO_NAME

    #######################
    ### PRIVATE OBJECTS ###
    #######################
    __access_token = ""
    __headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    __refresh_token_file = "refresh_token.json"

    ######################
    ### PUBLIC OBJECTS ###
    ######################
    logger = ""
    download_path = "~/Videos"

    def __init__(self):
        self.logger = youtube_logger()
        myauth = youtube_oauth()

        if not os.path.exists(constants.YTDLP):
            print(f"ERROR: Unable to locate yt-dlp at {constants.YTDLP}")
            self.logger.logger.error(
                f"ERROR: Unable to locate yt-dlp at {constants.YTDLP}"
            )
            exit(1)

        with open(self.__refresh_token_file, "r") as file:
            data = json.loads(file.readlines()[0])
            self.__access_token = data['access_token']
            self.__headers['Authorization'] = f"Bearer {self.__access_token}"

    def get_channel_id(self, needle):
        channel_id = -1
        endpoint = f"/youtube/v3/search?part=snippet&maxResults=5&q={needle}"
        url = f"{self.BASE_URL}{endpoint}"
        self.__headers['Authorization'] = f"Bearer {self.__access_token}"
        while channel_id == -1:
            r = requests.get(
                url=url, headers=self.__headers
            )
            if r.status_code == 200:
                response = json.loads(r.text)
                for i in response['items']:
                    if i['id']['kind'] == "youtube#channel":
                        if i['snippet']['title'].lower() == needle.lower():
                            channel_id = i['id']['channelId']
                            return channel_id

                if "nextPageToken" in response.keys():
                    next = response['nextPageToken']
                    endpoint = f"{endpoint}&nextPageToken={next}"
                    url = f"{self.BASE_URL}{endpoint}"
                    print(
                        "No channels found yet, searching the next page",
                        f"Search Term: {needle} :: Next Page: {next}"
                    )

                else:
                    print(
                        "No more results to search through!"
                    )
                    break

            else:
                print(
                    "ERROR: Unable to search for Channel ID!",
                    f"Status Code: {r.status_code} :: Details: {r.text}"
                )
                exit(1)

        print(
            "Unable to find a YouTube Channel with that name!"
        )
        exit(1)

    def search_videos(self, id, hours, titles=None):
        self.logger.logger.info(
            "Retrieving channel's Playlist ID..."
        )
        playlist_id = self.get_playlist_id(id)
        if not playlist_id:
            self.logger.logger.error(
                "Unable to find channel's Playlist ID!"
            )
            return False

        self.logger.logger.info(
            "Channel's Playlist ID retrieved successfully!"
        )
        self.logger.logger.info(
            "Retrieving channel's Playlist ID..."
        )
        videos = self.get_videos_in_playlist(playlist_id)
        if not videos:
            self.logger.logger.error(
                "Unable to get videos from channel's uploads playlist!"
            )
            return False

        self.logger.logger.info(
            "Parsing videos from uploads playlist..."
        )
        for video in videos:
            published_at = video['published_at']
            self.logger.logger.info(
                "Checking if video was released within the given timeframe..."
            )
            new_release = self.is_new_release(hours, published_at)
            if new_release:
                self.logger.logger.info(
                    "Video was released within the given timeframe!"
                )
                
                if titles:
                    self.logger.logger.info(
                        "Checking if video title matches the given title list..."
                    )
                    title_match = self.does_video_match(video['title'], titles)

                    if title_match:
                        self.logger.logger.info(
                            "Video title matches!"
                        )

                    else:
                        self.logger.logger.info(
                            "Video title does not match the given titles!"
                        )
                        break

                self.logger.logger.info(
                    "Dropping a like on the video..."
                )
                result = self.like_video(video['video_id'])
                i = 1
                while not result:
                    self.logger.logger.error(
                        "ERROR: Unable to leave a like on the video!"
                    )
                    i += 1
                    result = self.like_video(video['video_id'])
                    self.logger.logger.info(
                        f"Attempt #{i} of leaving a like..."
                    )
                    if i == 5:
                        self.logger.logger.error(
                            "ERROR: Unable to leave a like on the " +
                            "video after 5 attempts!"
                        )
                        break

                self.logger.logger.info(
                    "Liked the video successfully!"
                )
                self.logger.logger.info(
                    "Downloading the video..."
                )
                result = self.download_video(video['video_id'])
                i = 1
                while not result:
                    self.logger.logger.error(
                        "ERROR: Unable to download the video!"
                    )
                    i += 1
                    result = self.download_video(video['video_id'])
                    if i == 5:
                        self.logger.logger.error(
                            "ERROR: Unable to leave a like on the " +
                            "video after 5 attempts! You should " +
                            "download the video manually: " +
                            f"{video}"
                        )
                        break

                self.logger.logger.info(
                    "Downloaded the video successfully!"
                )

            else:
                self.logger.logger.info(
                    "Video was not released within the given timeframe!"
                )

    def download_video(self, id):
        base_url = "https://www.youtube.com"
        endpoint = f"/watch?v={id}"
        url = f"{base_url}{endpoint}"
        cmd = [
            constants.YTDLP, "--path", self.download_path, "--no-progress",
            "--format", self.FORMAT, "--output", self.NAME, id
        ]
        print(cmd)
        exit(1)
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if result.returncode == 0:
            return True

        else:
            return False

    def like_video(self, id):
        endpoint = f"/youtube/v3/videos/rate?id={id}&rating=like"
        url = f"{self.BASE_URL}{endpoint}"
        self.logger.logger.debug(
            "DEBUG Calling YouTube API to like the video..." +
            f"Video ID: {id} :: URL: {url} :: Headers: {self.__headers}"
        )
        r = requests.post(
            url=url, headers=self.__headers
        )
        if r.status_code == 204:
            self.logger.logger.debug(
                "DEBUG Successfully contacted the YouTube API! " +
                f"Status Code: {r.status_code} :: Details: {r.text}"
            )
            return True

        else:
            self.logger.logger.debug(
                "DEBUG Error contacting YouTube API! " +
                f"Status Code: {r.status_code} :: Details: {r.text}"
            )
            return False

    def get_playlist_id(self, id):
        endpoint = f"/youtube/v3/channels?part=contentDetails&id={id}"
        url = f"{self.BASE_URL}{endpoint}"
        self.logger.logger.debug(
            "DEBUG Calling YouTube API to retrieve the Playlist ID... " +
            f"Channel ID: {id} :: URL: {url} :: Headers: {self.__headers}"
        )
        r = requests.get(
            url=url, headers=self.__headers
        )
        if r.status_code == 200:
            self.logger.logger.debug(
                "DEBUG Successfully contacted YouTube API! " +
                f"Status Code: {r.status_code} :: Details: {r.text}"
            )
            data = json.loads(r.text)
            content_details = data['items'][0]['contentDetails']
            playlist_id = content_details['relatedPlaylists']['uploads']
            return playlist_id

        else:
            self.logger.logger.debug(
                "DEBUG Error contacting YouTube API! " +
                f"Status Code: {r.status_code} :: Details: {r.text}"
            )
            return False

    def get_videos_in_playlist(self, id):
        videos = []
        endpoint = "/youtube/v3/playlistItems?part=snippet&maxResults=10"
        endpoint = endpoint + f"&playlistId={id}"
        url = f"{self.BASE_URL}{endpoint}"
        self.logger.logger.debug(
            "DEBUG Calling YouTube API to retrieve videos in the " +
            f"uploads playlist... Channel ID: {id} :: URL: {url} " +
            f":: Headers: {self.__headers}"
        )
        r = requests.get(
            url=url, headers=self.__headers
        )
        if r.status_code == 200:
            self.logger.logger.debug(
                "DEBUG Successfully contacted YouTube API! " +
                f"Status Code: {r.status_code} :: Details: {r.text}"
            )
            data = json.loads(r.text)
            for i in data['items']:
                published_at = i['snippet']['publishedAt']
                video_id = i['snippet']['resourceId']['videoId']
                title = i['snippet']['title']
                videos.append({
                    "published_at": published_at,
                    "video_id": video_id,
                    "title": title
                })

            return videos

        else:
            self.logger.logger.debug(
                "DEBUG Error contacting YouTube API! " +
                f"Status Code: {r.status_code} :: Details: {r.text}"
            )
            return False

    def does_video_match(self, video_title, titles):
        for i in titles:
            title = i.lower()
            self.logger.logger.debug(
                f"DEBUG Checking to see if {title} matches " +
                f"{video_title.lower()}..."
            )
            if title in video_title.lower():
                self.logger.logger.debug(
                    f"DEBUG Found a matching title!"
                )
                return True
        self.logger.logger.debug(
            "DEBUG No video titles matched the configured titles!"
        )
        return False

    def is_new_release(self, hours, published_at):
        threshold = hours * 3600
        release_time = self.convert_time(published_at)
        now = time.time()
        timeframe = now - release_time
        if timeframe < threshold:
            return True
        return False

    def convert_time(self, published_at):
        return datetime.strptime(
            str(published_at), "%Y-%m-%dT%H:%M:%SZ"
        ).timestamp()