#!/usr/bin/env python3
import requests, json, pytz, os
from datetime import datetime, timezone
from youtubeLogger import youtubeLogger

class youtubeDL:
    'This class serves as a method to download videos from YouTube'

    # Note that there are no "private" objects or methods in the
    # Python class structure, but it is generally accepted that
    # methods and objects with a single "_" (underscore) preceding
    # the name indicates something "not to be messed with". So I'm
    # adopting that convention to denote "private" objects and methods
    
    #########################
    ### PRIVATE CONSTANTS ###
    #########################
    _FILE = ".creds"
    _TIME = 3600

    ########################
    ### PUBLIC CONSTANTS ###
    ########################
    BASE_URL = "youtube.googleapis.com"
    SCHEME = "https://"

    #######################
    ### PRIVATE OBJECTS ###
    #######################
    _apikey = ""
    _headers = {"Accept": "application/json"}
    _logger = youtubeLogger()

    ######################
    ### PUBLIC OBJECTS ###
    ######################
    debug = False # default is off, the main script will control if this is enabled or not
    playlist_id = "" # this will hold the content creator's "uploads" playlist id which we will need
    published_at = []
    resource_id = []
    title = []
    to_download = [] # this will be appended to for each video that needs to be downloaded

    def __init__(self):
        try:
            with open(self._FILE) as f:
                lines = f.readlines()
                self._apikey = lines[0].strip()
        except FileNotFoundError:
            self._logger.logMsg("ERROR: Unable to locate .creds file!")
            exit(1)

    def convertToEst(self, utc_timestamp):
        return datetime.fromisoformat(utc_timestamp[:-1]).replace(tzinfo=timezone.utc).astimezone(pytz.timezone("America/New_York")).strftime("%Y-%m-%dT%H:%M:%S")

    def convertTime(self, timestamp):
        return datetime.strptime(str(timestamp), "%Y-%m-%dT%H:%M:%S")

    def getCurrentTime(self):
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    def matchVideo(self, str):
        if "God of War" in str:
            return True
        else:
            return False

    def _channelJsonParser(self, data):
        # https://developers.google.com/youtube/v3/docs/channels#resource
        json_data = json.loads(data)
        try:
            self.playlist_id = json_data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
        except KeyError as e:
            self._logger.logMsg("ERROR: Unable to parse JSON response!")
            self._logger.logDebugMsg("DEBUG: Response Data: %s :: Error Details: %s" % (json_data, e))
            exit(1)

    def _playlistItemsJsonParser(self, data):
        # https://developers.google.com/youtube/v3/docs/playlistItems#resource
        json_data = json.loads(data)
        try:
            items = json_data["items"]
            for item in items:
                self.published_at.append(self.convertToEst(item["snippet"]["publishedAt"]))
                self.resource_id.append(item["snippet"]["resourceId"]["videoId"])
                self.title.append(item["snippet"]["title"])
        except KeyError as e:
            self._logger.logMsg("ERROR: Unable to parse JSON response!")
            self._logger.logDebugMsg("DEBUG: Response Data: %s :: Error Details: %s" % (json_data, e))
            exit(1)

    def getUploadsId(self, creator):
        # https://developers.google.com/youtube/v3/docs/channels/list?apix_params=%7B%22part%22%3A%5B%22contentDetails%22%5D%7D#request
        endpoint = "/youtube/v3/channels?part=contentDetails&forUsername=%s&key=%s" % (creator, self._apikey)
        url = self.SCHEME + self.BASE_URL + endpoint
        r = requests.get(url=url, headers=self._headers)
        if r.status_code == 200:
            self._logger.logMsg("Successfully found the uploads playlistId for: %s!" % creator)
            self._logger.logDebugMsg("DEBUG: Response Data: %s" % r.text)
            self._channelJsonParser(r.text)
        else:
            self._logger.logMsg("ERROR: Unable to find creator or unable to contact API!")
            self._logger.logDebugMsg("DEBUG: URL: %s :: HTTP Response: %d :: Response Data: %s" % (url, r.status_code, r.text))
            exit(1)

    def findVideos(self):
        # https://developers.google.com/youtube/v3/docs/playlistItems/list
        endpoint = "/youtube/v3/playlistItems?part=snippet&playlistId=%s&key=%s" % (self.playlist_id, self._apikey)
        url = self.SCHEME + self.BASE_URL + endpoint
        r = requests.get(url=url, headers=self._headers)
        if r.status_code == 200:
            self._logger.logMsg("Successfully retrieved the 5 most recent videos...")
            self._logger.logDebugMsg("DEBUG: Response Data: %s" % r.text)
            self._playlistItemsJsonParser(r.text)
        else:
            self._logger.logMsg("ERROR: Unable to retrieve a list of videos or unable to contact API!")
            self._logger.logDebugMsg("DEBUG: URL: %s :: HTTP Response: %d :: Response Data: %s" % (url, r.status_code, r.text))

    def parseVideos(self):
        now = self.getCurrentTime()
        i = 0
        while i < 5:
            test = self.convertTime(now).timestamp() - self.convertTime(self.published_at[i]).timestamp()
            if test < self._TIME:
                self._logger.logMsg("Found a newly released video! Checking to see if it matches our criteria...")
                self._logger.logDebugMsg("DEBUG: Published At: %s :: Title: %s :: Id: %s" % (self.published_at[i], self.title[i], self.resource_id[i]))
                if self.matchVideo(self.title[i]):
                    self._logger.logMsg("The video matches our criteria! Adding video to the download queue...")
                    self._logger.logDebugMsg("DEBUG: Appending Video ID: %s to the to_download list..." % self.resource_id[i])
                    self.to_download.append(self.resource_id[i])
                else:
                    self._logger.logMsg("The video does NOT match our criteria! Moving to next video...")
            else:
                self._logger.logMsg("Video: %s is not a new release! Moving to next video..." % self.resource_id[i])
            i+=1

    def downloadVideos(self):
        for i in self.to_download:
            url = "https://www.youtube.com/watch?v=%s" % i
            self._logger.logMsg("Starting download through yt-dlp...")
            self._logger.logDebugMsg("DEBUG: Downloading Video ID: %s..." % i, 1)
            cmd = "/usr/local/bin/yt-dlp --path /home/benjamin/ --no-progress --format 315+140 %s" % url
            os.system(cmd)

    def rateVideos(self, access_token):
        'This method is used to leave a rating on specific YouTube Video IDs. In our case, we will only be leaving "likes"'
        # https://developers.google.com/youtube/v3/docs/videos/rate
        endpoint = "/youtube/v3/videos/rate?"
        headers = {"Accept": "application/json", "Authorization": ""}
        headers["Authorization"] = f"Bearer {access_token}"
        for i in self.to_download:
            url = self.SCHEME + self.BASE_URL + endpoint + f"id={i}&rating=like&key={self._apikey}"
            r = requests.post(url=url, headers=headers)
            if r.status_code == 204:
                self._logger.logMsg(f"Successfully liked video {i}")
            else:
                self._logger.logMsg("ERROR: Unable to leave a rating on the video!")
                self._logger.logDebugMsg(f"DEBUG: HTTP Response: {r.status_code} :: Access Token: {access_token} :: Video ID: {i} :: Response Text: {r.text}")