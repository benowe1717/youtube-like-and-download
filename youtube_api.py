#!/usr/bin/env python3
import constants
from logger import youtube_logger
from auth import youtube_oauth
import json, requests

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

    def __init__(self):
        self.logger = youtube_logger()
        youtube_oauth()

        with open(self.__refresh_token_file, "r") as file:
            data = json.loads(file.readlines()[0])
            self.__access_token = data['access_token']

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